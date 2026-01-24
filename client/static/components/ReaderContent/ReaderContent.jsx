import { forwardRef } from 'preact/compat'
import { useRef, useImperativeHandle, useEffect } from 'preact/hooks'
import Progress from '../Progress/Progress'
import './ReaderContent.css'

// NOTE: findBookmark relies on nodes being processed in document order.
// This enables an O(n+m) merge scan. Do not use if render order changes.
function createBookmarkFinder(segments) {
  let idx = 0
  return function findAtOffset(start, length) {
    const end = start + length
    while (idx < segments.length && segments[idx].start < start) {
      idx++
    }
    if (idx < segments.length && segments[idx].start < end) {
      return segments[idx].name
    }
    return null
  }
}

function renderNode(node, key, annotations) {
  if (node.type === 'text') {
    if (node.text === '\n') return null

    const bookmark = annotations.findBookmark(node.start, node.length)

    return (
      <span
        key={key}
        data-bookmark={bookmark || undefined}
        ref={(el) => {
          const text = el?.firstChild
          if (text?.nodeType === Node.TEXT_NODE) {
            text.__start = node.start
            annotations.textNodeIndex.push({
              node: text,
              start: node.start,
              end: node.start + node.length,
            })
          }
        }}
      >
        {node.text}
      </span>
    )
  }

  if (node.type === 'void') {
    if (node.tag === 'br') return <br key={key} />
    if (node.tag === 'hr') return <hr key={key} />
    return null
  }

  if (node.type === 'anchor') {
    const bookmark = annotations.findBookmark(node.start, 1)
    return (
      <img
        key={key}
        src={node.src}
        alt={node.alt || ''}
        data-bookmark={bookmark || undefined}
        ref={(el) => {
          if (el) el.__start = node.start
        }}
      />
    )
  }

  if (node.type === 'element') {
    const Tag = node.tag
    const children = node.children.map((c, i) => renderNode(c, i, annotations)).filter(Boolean)
    return <Tag key={key}>{children}</Tag>
  }

  return null
}

function renderContentTree(tree, annotations) {
  if (!tree || !Array.isArray(tree)) return null
  return tree.map((node, i) => renderNode(node, i, annotations)).filter(Boolean)
}

export const ReaderContent = forwardRef(function ReaderContent(
  { article, progress, settings, bookmarks = [] },
  ref,
) {
  const { font, size, spacing } = settings
  const containerRef = useRef(null)
  const textNodeIndexRef = useRef([])

  const hasContentTree = article?.content_tree && Array.isArray(article.content_tree)

  // Precompute bookmark segments (exclude furthest - it doesn't need data-bookmark)
  const bookmarkSegments = Array.isArray(bookmarks)
    ? bookmarks
        .filter((b) => b.start != null && b.name !== 'furthest')
        .map((b) => ({ start: b.start, name: b.name }))
        .sort((a, b) => a.start - b.start)
    : []

  // Clear text node index before each render
  textNodeIndexRef.current = []

  const annotations = {
    findBookmark: createBookmarkFinder(bookmarkSegments),
    highlights: [],
    textNodeIndex: textNodeIndexRef.current,
  }

  // --- Private helpers ---

  // Binary search for text node containing offset
  const findTextNodeByOffset = (offset) => {
    const arr = textNodeIndexRef.current
    let low = 0
    let high = arr.length - 1
    while (low <= high) {
      const mid = (low + high) >>> 1
      const entry = arr[mid]
      if (offset < entry.start) {
        high = mid - 1
      } else if (offset >= entry.end) {
        low = mid + 1
      } else {
        return entry
      }
    }
    return null
  }

  // Probe viewport to find first fully visible text node's offset
  const getFirstVisibleOffset = () => {
    const container = containerRef.current
    if (!container) return null

    const rect = container.getBoundingClientRect()
    const x = rect.left + rect.width / 2

    // Start 50px down to skip partially-scrolled text at the top
    for (let y = rect.top + 50; y < rect.bottom; y += 10) {
      const range = document.caretRangeFromPoint?.(x, y)
      const caret = document.caretPositionFromPoint?.(x, y)

      const textNode = range?.startContainer ?? caret?.offsetNode
      const localOffset = range?.startOffset ?? caret?.offset

      if (textNode?.nodeType === Node.TEXT_NODE && textNode.__start != null) {
        return textNode.__start + localOffset
      }
    }
    return null
  }

  // --- Public API ---
  useImperativeHandle(ref, () => ({
    get contentContainer() {
      return containerRef.current
    },

    getReaderLocation() {
      return getFirstVisibleOffset()
    },

    jumpToBookmark(bookmark) {
      const container = containerRef.current
      if (!container) return false

      // Offset-based bookmark
      if (bookmark.start != null) {
        // Furthest has no data-bookmark attr, use binary search
        if (bookmark.name === 'furthest') {
          const entry = findTextNodeByOffset(bookmark.start)
          if (entry?.node?.parentElement) {
            entry.node.parentElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
            return true
          }
        } else {
          // User bookmarks have data-bookmark attribute
          const el = container.querySelector(`[data-bookmark="${bookmark.name}"]`)
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' })
            return true
          }
        }
      }

      // Legacy percentage-based bookmark
      if (bookmark.legacy != null) {
        const scrollHeight = container.scrollHeight - container.clientHeight
        const scrollTop = (bookmark.legacy / 100) * scrollHeight
        container.scrollTo({ top: scrollTop, behavior: 'smooth' })
        return true
      }

      return false
    },
  }))

  // Jump to furthest on article load
  useEffect(() => {
    if (!hasContentTree || textNodeIndexRef.current.length === 0) return

    const furthest = bookmarks?.find((b) => b.name === 'furthest')
    if (!furthest?.start) return

    const entry = findTextNodeByOffset(furthest.start)
    if (entry?.node?.parentElement) {
      entry.node.parentElement.scrollIntoView({ behavior: 'instant', block: 'start' })
    }
  }, [article?.uuid])

  return (
    <div className="reader-content" ref={containerRef}>
      <Progress value={progress} className="reader-progress-bar" />

      <article className={`reader-article ${font} size-${size} ${spacing}`}>
        <h1>{article?.title}</h1>
        {hasContentTree ? (
          <div>{renderContentTree(article.content_tree, annotations)}</div>
        ) : (
          <div dangerouslySetInnerHTML={{ __html: article?.content || '' }} />
        )}
      </article>

      <div className="reader-bottom-bar">
        <span className="reader-bottom-title">{article?.title}</span>
        <span className="reader-bottom-progress">{Math.round(progress)}%</span>
      </div>
    </div>
  )
})
