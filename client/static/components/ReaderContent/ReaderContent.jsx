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
      return { name: segments[idx].name, start: segments[idx].start }
    }
    return null
  }
}

// Build highlight segments using sweep line algorithm
function buildHighlightSegments(highlights) {
  if (!highlights || highlights.length === 0) return []

  // Create events (sort highlights by created_date first so active array maintains order)
  const sortedHighlights = [...highlights]
    .filter((h) => h.start != null && h.end != null)
    .sort((a, b) => new Date(a.created_date) - new Date(b.created_date))

  const events = []
  for (const h of sortedHighlights) {
    events.push({ pos: h.start, type: 'start', highlight: h })
    events.push({ pos: h.end, type: 'end', highlight: h })
  }

  // Sort by position; at same position, ends come before starts
  events.sort((a, b) => {
    if (a.pos !== b.pos) return a.pos - b.pos
    return a.type === 'end' ? -1 : 1
  })

  // Sweep
  const active = []
  const segments = []
  let lastPos = null

  for (const event of events) {
    if (active.length > 0 && lastPos !== null && lastPos !== event.pos) {
      segments.push({ start: lastPos, end: event.pos, activeHighlights: [...active] })
    }

    if (event.type === 'start') {
      active.push(event.highlight)
    } else {
      const idx = active.indexOf(event.highlight)
      if (idx !== -1) active.splice(idx, 1)
    }

    lastPos = event.pos
  }

  return segments
}

// Merge-scan finder for highlight segments (relies on document order traversal)
function createHighlightSegmentFinder(segments) {
  let idx = 0
  return function findSegmentsInRange(start, end) {
    // Advance past segments that end before our range
    while (idx < segments.length && segments[idx].end <= start) {
      idx++
    }

    // Collect segments that overlap with our range
    const result = []
    let i = idx
    while (i < segments.length && segments[i].start < end) {
      result.push(segments[i])
      i++
    }
    return result
  }
}

function renderTextSpan(text, start, end, bookmarkName, highlights, annotations, key) {
  const highlightIds = highlights.length > 0 ? highlights.map((h) => h.uuid).join(' ') : undefined

  return (
    <span
      key={key}
      data-bookmark={bookmarkName || undefined}
      data-highlights={highlightIds}
      className={highlightIds ? 'reader-highlight' : undefined}
      ref={(el) => {
        if (!el) return
        const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)
        const textNode = walker.nextNode()
        if (textNode) {
          textNode.__start = start
          annotations.textNodeIndex.push({ node: textNode, start, end })
        }
      }}
    >
      {text}
    </span>
  )
}

function renderNode(node, key, annotations) {
  if (node.type === 'text') {
    if (node.text === '\n') return null

    const textStart = node.start
    const textEnd = textStart + node.length
    const bookmark = annotations.findBookmark(textStart, node.length)
    const segments = annotations.findHighlightSegments(textStart, textEnd)

    // No highlights - render simple span
    if (segments.length === 0) {
      return renderTextSpan(node.text, textStart, textEnd, bookmark?.name, [], annotations, key)
    }

    // Build pieces from segment boundaries clipped to text range
    const pieces = []
    let pos = textStart

    for (const seg of segments) {
      // Gap before this segment (unhighlighted)
      if (pos < seg.start) {
        const gapEnd = Math.min(seg.start, textEnd)
        pieces.push({
          start: pos,
          end: gapEnd,
          text: node.text.slice(pos - textStart, gapEnd - textStart),
          highlights: [],
        })
        pos = gapEnd
      }

      // Segment portion within text range
      const segStart = Math.max(seg.start, textStart)
      const segEnd = Math.min(seg.end, textEnd)
      if (segStart < segEnd) {
        pieces.push({
          start: segStart,
          end: segEnd,
          text: node.text.slice(segStart - textStart, segEnd - textStart),
          highlights: seg.activeHighlights,
        })
        pos = segEnd
      }
    }

    // Remaining gap after last segment
    if (pos < textEnd) {
      pieces.push({
        start: pos,
        end: textEnd,
        text: node.text.slice(pos - textStart, textEnd - textStart),
        highlights: [],
      })
    }

    // Assign bookmark to the piece that contains it
    return pieces.map((p, i) => {
      const hasBookmark = bookmark && bookmark.start >= p.start && bookmark.start < p.end
      return renderTextSpan(p.text, p.start, p.end, hasBookmark ? bookmark.name : null, p.highlights, annotations, `${key}-${i}`)
    })
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
        data-bookmark={bookmark?.name || undefined}
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
  { article, progress, settings, bookmarks = [], highlights = [], onHighlightClick, scrollToHighlight },
  ref,
) {
  const { font, size, spacing } = settings
  const containerRef = useRef(null)
  const textNodeIndexRef = useRef([])

  // Precompute bookmark segments (exclude furthest - it doesn't need data-bookmark)
  const bookmarkSegments = Array.isArray(bookmarks)
    ? bookmarks
        .filter((b) => b.start != null && b.name !== 'furthest')
        .map((b) => ({ start: b.start, name: b.name }))
        .sort((a, b) => a.start - b.start)
    : []

  // Precompute highlight segments using sweep line
  const highlightSegments = buildHighlightSegments(highlights)

  // Clear text node index before each render
  textNodeIndexRef.current = []

  const annotations = {
    findBookmark: createBookmarkFinder(bookmarkSegments),
    findHighlightSegments: createHighlightSegmentFinder(highlightSegments),
    textNodeIndex: textNodeIndexRef.current,
  }

  // --- Private helpers ---

  // Binary search for text node containing offset
  const findTextNodeByOffset = (offset) => {
    const arr = textNodeIndexRef.current
    if (arr.length === 0) return null

    // Clamp to last node if offset is past end of content
    if (offset >= arr[arr.length - 1].end) {
      return arr[arr.length - 1]
    }

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

  // Jump to highlight (if specified) or furthest on article load
  useEffect(() => {
    if (textNodeIndexRef.current.length === 0) return
    const container = containerRef.current
    if (!container) return

    // If scrollToHighlight is set, scroll to that highlight
    if (scrollToHighlight) {
      const el = container.querySelector(`[data-highlights~="${scrollToHighlight}"]`)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
        el.classList.add('highlight-active')
      }
      return
    }

    // Otherwise scroll to furthest bookmark
    const furthest = bookmarks?.find((b) => b.name === 'furthest')
    if (!furthest?.start) return

    const entry = findTextNodeByOffset(furthest.start)
    if (entry?.node?.parentElement) {
      entry.node.parentElement.scrollIntoView({ behavior: 'instant', block: 'start' })
    }
  }, [article?.uuid, scrollToHighlight])

  // Highlight hover and click handlers
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    let activeId = null

    const onEnter = (e) => {
      const target = e.target.closest('[data-highlights]')
      if (!target) return

      const ids = target.dataset.highlights.split(' ')
      const id = ids[ids.length - 1] // Most recent highlight
      if (id === activeId) return

      // Clear previous
      if (activeId) {
        container.querySelectorAll('.highlight-active').forEach((el) => el.classList.remove('highlight-active'))
      }

      activeId = id
      container.querySelectorAll(`[data-highlights~="${id}"]`).forEach((el) => el.classList.add('highlight-active'))
    }

    const onLeave = (e) => {
      if (!activeId) return
      const related = e.relatedTarget?.closest?.('[data-highlights]')
      if (related?.dataset.highlights?.includes(activeId)) return

      container.querySelectorAll('.highlight-active').forEach((el) => el.classList.remove('highlight-active'))
      activeId = null
    }

    const onClick = (e) => {
      const target = e.target.closest('[data-highlights]')
      if (!target) return

      const ids = target.dataset.highlights.split(' ')
      const highlightId = ids[ids.length - 1] // Most recent highlight
      onHighlightClick?.(highlightId)
    }

    container.addEventListener('mouseenter', onEnter, true)
    container.addEventListener('mouseleave', onLeave, true)
    container.addEventListener('click', onClick)
    return () => {
      container.removeEventListener('mouseenter', onEnter, true)
      container.removeEventListener('mouseleave', onLeave, true)
      container.removeEventListener('click', onClick)
    }
  }, [onHighlightClick])

  return (
    <div className="reader-content" ref={containerRef}>
      <Progress value={progress} className="reader-progress-bar" />

      <article className={`reader-article ${font} size-${size} ${spacing}`}>
        <h1>{article?.title}</h1>
        <div>{renderContentTree(article?.content_tree || [], annotations)}</div>
      </article>

      <div className="reader-bottom-bar">
        <span className="reader-bottom-title">{article?.title}</span>
        <span className="reader-bottom-progress">{Math.round(progress)}%</span>
      </div>
    </div>
  )
})
