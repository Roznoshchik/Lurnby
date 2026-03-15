import { useState, useRef, useCallback, useEffect } from 'preact/hooks'
import alert from '../services/alertService'
import { api } from '../services/api'
import { ROUTES } from '../services/routes'

/**
 * Hook for handling text selection and highlight creation in the reader.
 *
 * @param {RefObject} contentRef - Ref to ReaderContent imperative handle
 * @param {string} articleUuid - Article UUID for API calls
 * @param {boolean} loading - Whether article is still loading
 * @param {Function} onHighlightCreated - Callback when highlight is created
 */
export function useReaderHighlights(contentRef, articleUuid, loading, onHighlightCreated) {
  const [popoverOpen, setPopoverOpen] = useState(false)
  const [selectionRect, setSelectionRect] = useState(null)
  const selectionDataRef = useRef(null)

  const handleSelectionEnd = useCallback(() => {
    const selection = window.getSelection()
    if (!selection.rangeCount || selection.isCollapsed) {
      setPopoverOpen(false)
      return
    }

    const range = selection.getRangeAt(0)
    const container = contentRef.current?.contentContainer

    // Check selection is within reader content
    if (!container?.contains(range.commonAncestorContainer)) {
      setPopoverOpen(false)
      return
    }

    // Get offsets from text nodes with __start and __chunkIdx
    const startNode = range.startContainer
    const endNode = range.endContainer

    if (
      startNode.__start == null ||
      endNode.__start == null ||
      startNode.__chunkIdx == null ||
      endNode.__chunkIdx == null
    ) {
      setPopoverOpen(false)
      return
    }

    const startChunk = startNode.__chunkIdx
    const start = startNode.__start + range.startOffset
    const endChunk = endNode.__chunkIdx
    const end = endNode.__start + range.endOffset
    const text = selection.toString().trim()

    if (!text) {
      setPopoverOpen(false)
      return
    }

    // Store selection data for highlight creation (chunk-based offsets)
    selectionDataRef.current = { text, start_chunk: startChunk, start, end_chunk: endChunk, end }

    // Position popover at end of selection (last line for multi-line)
    const rects = range.getClientRects()
    const rect = rects[rects.length - 1]
    setSelectionRect(rect)
    setPopoverOpen(true)
  }, [contentRef])

  // Attach selection event listeners
  useEffect(() => {
    if (loading) return

    const container = contentRef.current?.contentContainer
    if (!container) return

    container.addEventListener('mouseup', handleSelectionEnd)
    container.addEventListener('touchend', handleSelectionEnd)

    return () => {
      container.removeEventListener('mouseup', handleSelectionEnd)
      container.removeEventListener('touchend', handleSelectionEnd)
    }
  }, [contentRef, handleSelectionEnd, loading])

  const clearSelection = useCallback(() => {
    window.getSelection().removeAllRanges()
    setPopoverOpen(false)
    selectionDataRef.current = null
  }, [])

  const createHighlight = useCallback(async () => {
    const data = selectionDataRef.current
    if (!data) return

    try {
      const { data: response } = await api.post(ROUTES.API.HIGHLIGHTS, {
        article_uuid: articleUuid,
        text: data.text,
        start_chunk: data.start_chunk,
        start: data.start,
        end_chunk: data.end_chunk,
        end: data.end,
      })
      alert.success('Highlight created')
      clearSelection()
      onHighlightCreated?.(response.highlight)
    } catch (err) {
      console.error('Error creating highlight:', err)
      alert.error('Failed to create highlight')
    }
  }, [articleUuid, clearSelection, onHighlightCreated])

  const openHighlightModal = useCallback(() => {
    // TODO: Return data for modal, let parent handle modal state
    const data = selectionDataRef.current
    clearSelection()
    return data
  }, [clearSelection])

  return {
    popoverOpen,
    setPopoverOpen,
    selectionRect,
    createHighlight,
    openHighlightModal,
    selectionData: selectionDataRef.current,
  }
}
