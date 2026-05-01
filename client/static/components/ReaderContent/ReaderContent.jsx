import { forwardRef } from 'preact/compat'
import { useRef, useImperativeHandle, useEffect, useMemo } from 'preact/hooks'
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
  let lastStart = -1
  return function findSegmentsInRange(start, end) {
    // Reset if we're going backwards (new traversal from beginning)
    if (start < lastStart) {
      idx = 0
    }
    lastStart = start

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

function renderTextSpan(text, start, end, chunkIdx, bookmarkName, highlights, annotations, key) {
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
          textNode.__chunkIdx = chunkIdx
          textNode.__start = start
          annotations.textNodeIndex.push({ node: textNode, start, end })
        }
      }}
    >
      {text}
    </span>
  )
}

function renderNode(node, key, chunkIdx, annotations) {
  if (node.type === 'text') {
    if (node.text === '\n') return null

    const textStart = node.start
    const textEnd = textStart + node.length
    const bookmark = annotations.findBookmark(textStart, node.length)
    const segments = annotations.findHighlightSegments(textStart, textEnd)

    // No highlights - render simple span
    if (segments.length === 0) {
      return renderTextSpan(node.text, textStart, textEnd, chunkIdx, bookmark?.name, [], annotations, key)
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
      return renderTextSpan(p.text, p.start, p.end, chunkIdx, hasBookmark ? bookmark.name : null, p.highlights, annotations, `${key}-${i}`)
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
          if (el) {
            el.__chunkIdx = chunkIdx
            el.__start = node.start
          }
        }}
      />
    )
  }

  if (node.type === 'element') {
    const Tag = node.tag
    const children = node.children.map((c, i) => renderNode(c, i, chunkIdx, annotations)).filter(Boolean)
    return <Tag key={key}>{children}</Tag>
  }

  return null
}

function renderContentTree(tree, chunkIdx, annotations) {
  if (!tree || !Array.isArray(tree)) return null
  return tree.map((node, i) => renderNode(node, i, chunkIdx, annotations)).filter(Boolean)
}

export const ReaderContent = forwardRef(function ReaderContent(
  { title, chunks = [], progress, settings, bookmarks = [], highlights = [], onHighlightClick },
  ref,
) {
  const { font, size, spacing } = settings
  const containerRef = useRef(null)
  // Text node index per chunk: { [chunkIdx]: [{ node, start, end }] }
  const textNodeIndicesRef = useRef({})

  // Track which chunks we've seen to detect actual chunk changes
  const seenChunksRef = useRef(new Set())

  // Build per-chunk annotations (finders + text node array)
  const chunkAnnotations = useMemo(() => {
    const result = {}
    const currentChunks = new Set(chunks.map(c => c.idx))

    for (const chunk of chunks) {
      // Reset text node array if this is a new chunk (not seen before)
      if (!seenChunksRef.current.has(chunk.idx)) {
        textNodeIndicesRef.current[chunk.idx] = []
        seenChunksRef.current.add(chunk.idx)
      }

      // Filter bookmarks for this chunk (exclude furthest - it doesn't need data-bookmark)
      const chunkBookmarks = bookmarks
        .filter((b) => b.chunk === chunk.idx && b.offset != null && b.name !== 'furthest')
        .map((b) => ({ start: b.offset, name: b.name }))
        .sort((a, b) => a.start - b.start)

      // Filter highlights that touch this chunk
      const chunkHighlights = highlights.filter(
        (h) => h.start_chunk != null && h.start_chunk <= chunk.idx && h.end_chunk >= chunk.idx,
      )

      // Clip highlight offsets to this chunk's boundaries
      const clippedHighlights = chunkHighlights.map((h) => ({
        ...h,
        start: h.start_chunk === chunk.idx ? h.start : 0,
        end: h.end_chunk === chunk.idx ? h.end : chunk.text_length,
      }))

      const segments = buildHighlightSegments(clippedHighlights)

      result[chunk.idx] = {
        findBookmark: createBookmarkFinder(chunkBookmarks),
        findHighlightSegments: createHighlightSegmentFinder(segments),
        textNodeIndex: textNodeIndicesRef.current[chunk.idx],
      }
    }

    // Clean up text node indices for chunks that are no longer loaded
    for (const idx of seenChunksRef.current) {
      if (!currentChunks.has(idx)) {
        delete textNodeIndicesRef.current[idx]
        seenChunksRef.current.delete(idx)
      }
    }

    return result
  }, [chunks, bookmarks, highlights])

  // --- Private helpers ---

  // Binary search for text node containing offset in a specific chunk
  const findTextNodeInChunk = (chunkIdx, offset) => {
    const arr = textNodeIndicesRef.current[chunkIdx]
    if (!arr || arr.length === 0) {
      return null
    }

    // Clamp to last node if offset is past end
    if (offset >= arr[arr.length - 1].end) {
      return arr[arr.length - 1]
    }

    // Clamp to first node if offset is before start
    if (offset < arr[0].start) {
      return arr[0]
    }

    let low = 0
    let high = arr.length - 1
    while (low <= high) {
      const mid = (low + high) >>> 1
      const entry = arr[mid]
      if (offset < entry.start) {
        high = mid - 1
      } else if (offset > entry.end) {
        low = mid + 1
      } else {
        return entry
      }
    }

    // Binary search failed - offset is in a gap (void element)
    // Return the closest node
    let closestIdx = Math.min(low, arr.length - 1)
    return arr[closestIdx]
  }

  // Probe viewport to find text position at specified location (top/middle/bottom)
  const getFirstVisiblePosition = (position = 'top') => {
    const container = containerRef.current
    if (!container) return null

    const rect = container.getBoundingClientRect()
    const x = rect.left + rect.width / 2

    let y
    if (position === 'top') {
      y = rect.top + 20 // Small offset from top to avoid header/padding
    } else if (position === 'middle') {
      y = rect.top + rect.height / 2
    } else if (position === 'bottom') {
      y = rect.bottom - 20 // Small offset from bottom to avoid footer/padding
    }

    // Probe at specified position
    const range = document.caretRangeFromPoint?.(x, y)
    const caret = document.caretPositionFromPoint?.(x, y)

    const textNode = range?.startContainer ?? caret?.offsetNode
    const localOffset = range?.startOffset ?? caret?.offset

    if (textNode?.nodeType === Node.TEXT_NODE && textNode.__chunkIdx != null && textNode.__start != null) {
      return {
        chunk: textNode.__chunkIdx,
        offset: textNode.__start + localOffset,
      }
    }

    return null
  }

  // --- Public API ---
  useImperativeHandle(ref, () => ({
    get contentContainer() {
      return containerRef.current
    },

    // Returns current reading position { chunk, offset }
    getReaderLocation() {
      return getFirstVisiblePosition()
    },

    // Returns number of text nodes indexed for a chunk
    getTextNodeCount(chunkIdx) {
      return textNodeIndicesRef.current[chunkIdx]?.length || 0
    },

    // Scrolls to position (assumes chunk is already rendered)
    scrollToPosition({ chunk, offset, behavior = 'smooth' }) {
      const entry = findTextNodeInChunk(chunk, offset)
      if (!entry?.node) return false
      const container = containerRef.current
      if (!container) return false
      const charOffset = Math.min(Math.max(0, offset - entry.start), entry.node.textContent.length)
      const range = document.createRange()
      range.setStart(entry.node, charOffset)
      range.collapse(true)
      const rect = range.getBoundingClientRect()
      const containerRect = container.getBoundingClientRect()
      const targetScrollTop = container.scrollTop + rect.top - containerRect.top - 80
      container.scrollTo({ top: Math.max(0, targetScrollTop), behavior })
      return true
    },
  }))

  // Initial scroll is now handled by reader.jsx after ensuring chunks are loaded
  // ReaderContent just exposes scrollToPosition() and scrollToHighlight()

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
        {chunks.map((chunk) => (
          <div key={chunk.idx} data-chunk={chunk.idx}>
            {renderContentTree(chunk.content_tree, chunk.idx, chunkAnnotations[chunk.idx])}
          </div>
        ))}
      </article>

      <div className="reader-bottom-bar">
        <span className="reader-bottom-title">{title}</span>
        <span className="reader-bottom-progress">{Math.round(progress)}%</span>
      </div>
    </div>
  )
})
