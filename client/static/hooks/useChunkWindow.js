import { useState, useRef, useEffect, useCallback } from 'preact/hooks'
import { api } from '../services/api'
import { ROUTES } from '../services/routes'

// Count text nodes in content tree
function countTextNodesInTree(tree) {
  if (!tree || !Array.isArray(tree)) return 0
  let count = 0

  const traverse = (node) => {
    if (node.type === 'text' && node.text !== '\n') {
      count++
    } else if (node.type === 'element' && node.children) {
      node.children.forEach(traverse)
    }
  }

  tree.forEach(traverse)
  return count
}

/**
 * Hook for managing chunk window - loads/unloads chunks based on scroll position
 * and provides Promise-based navigation.
 *
 * @param {Object} options
 * @param {Object} options.contentRef - Ref to ReaderContent component
 * @param {string} options.articleUuid - Article UUID (always available, from URL params)
 * @param {Object} options.article - Article object with chunks_meta (may be null initially)
 * @param {Function} options.onHighlightsLoaded - Callback when highlights are loaded with chunks
 * @returns {Object} { chunks, jumpToPosition }
 */
export function useChunkWindow({ contentRef, articleUuid, article, onHighlightsLoaded }) {
  const [chunks, setChunks] = useState({})
  const chunksRef = useRef({}) // Mirror state for stable access without stale closures
  const loadingRef = useRef(false)
  const isJumpingRef = useRef(false) // Suspend windowing during jumps

  // Keep chunksRef in sync with state
  useEffect(() => {
    chunksRef.current = chunks
  }, [chunks])

  // Internal: Load chunks from API and update state
  // Position maintenance happens HERE, not in effect
  const loadChunks = useCallback(
    async (chunkIndices) => {
      if (loadingRef.current) return
      loadingRef.current = true

      try {
        // 1. Capture position BEFORE chunk update
        const prevPosition = contentRef.current?.getReaderLocation?.()

        // 2. Use chunksRef (not stale closure) to determine what to fetch
        const currentChunks = Object.keys(chunksRef.current).map(Number)
        const toFetch = chunkIndices.filter((idx) => !currentChunks.includes(idx))

        // 3. Check if adding chunks above (compute BEFORE setChunks)
        const addingAbove =
          chunkIndices.some(
            (idx) => !currentChunks.includes(idx) && currentChunks.length > 0 && idx < Math.min(...currentChunks),
          )

        // 4. Fetch from API if needed
        if (toFetch.length > 0) {
          const results = await Promise.all(
            toFetch.map((idx) => api.get(ROUTES.API.articleChunk(articleUuid, idx))),
          )

          const newChunks = {}
          const newHighlights = []
          for (const { data } of results) {
            newChunks[data.chunk.idx] = data.chunk
            if (data.highlights) newHighlights.push(...data.highlights)
          }

          // 5. Update chunks state (functional update for safety)
          setChunks((prev) => {
            const updated = {}
            for (const idx of chunkIndices) {
              if (prev[idx]) updated[idx] = prev[idx]
              if (newChunks[idx]) updated[idx] = newChunks[idx]
            }
            return updated
          })

          // Notify highlights loaded
          if (newHighlights.length > 0 && onHighlightsLoaded) {
            onHighlightsLoaded(newHighlights)
          }

          // 6. Restore position after DOM updates (RAF guarantees layout committed)
          if (addingAbove && prevPosition && !isJumpingRef.current) {
            requestAnimationFrame(() => {
              contentRef.current?.scrollToPosition?.({
                chunk: prevPosition.chunk,
                offset: prevPosition.offset,
                behavior: 'instant',
              })
            })
          }
        } else {
          // No new chunks to load, but still need to filter to requested chunks
          setChunks((prev) => {
            const filtered = {}
            for (const idx of chunkIndices) {
              if (prev[idx]) filtered[idx] = prev[idx]
            }
            return filtered
          })
        }
      } finally {
        loadingRef.current = false
      }
    },
    [articleUuid, contentRef, onHighlightsLoaded],
  )

  // Internal: Wait for chunk to be in state and text nodes to be indexed
  const waitForReady = useCallback(
    async (chunkIdx) => {
      return new Promise((resolve) => {
        let attempts = 0
        const maxAttempts = 100 // 5 seconds
        let expectedCount = null

        const retry = () => {
          if (attempts >= maxAttempts) {
            console.warn(`Timeout waiting for chunk ${chunkIdx}`)
            resolve(false)
          } else {
            attempts++
            setTimeout(check, 50)
          }
        }

        const check = () => {
          const chunk = chunksRef.current[chunkIdx]

          if (!chunk) {
            retry()
            return
          }

          if (expectedCount === null) {
            expectedCount = countTextNodesInTree(chunk.content_tree)
          }

          const actual = contentRef.current?.getTextNodeCount?.(chunkIdx) || 0
          if (actual >= expectedCount) resolve(true)
          else retry()
        }

        check()
      })
    },
    [contentRef],
  )

  // Determine which chunks to load based on position
  const getChunksToLoad = useCallback(
    (chunkIdx, offset) => {
      if (!article?.chunks_meta) return [chunkIdx]
      const chunkMeta = article.chunks_meta[chunkIdx]
      if (!chunkMeta) return [chunkIdx]

      const pct = (offset / chunkMeta.text_length) * 100
      const chunkCount = article.chunks_meta.length

      if (pct < 20 && chunkIdx > 0) return [chunkIdx - 1, chunkIdx]
      if (pct > 80 && chunkIdx < chunkCount - 1) return [chunkIdx, chunkIdx + 1]
      return [chunkIdx]
    },
    [article?.chunks_meta],
  )

  // Automatic windowing (synchronous, non-blocking, suspended during jumps)
  useEffect(() => {
    const container = contentRef.current?.contentContainer
    if (!container || !article?.chunks_meta) return

    let rafId = null

    const handleScroll = () => {
      // Skip if jumping
      if (isJumpingRef.current) return

      if (rafId) return
      rafId = requestAnimationFrame(() => {
        rafId = null

        // Get currently loaded chunks
        const currentChunks = Object.values(chunksRef.current).sort((a, b) => a.idx - b.idx)
        if (currentChunks.length === 0) return

        const scrollableHeight = container.scrollHeight - container.clientHeight
        if (scrollableHeight <= 0) return // No scrolling needed

        const scrollPct = container.scrollTop / scrollableHeight
        const firstLoadedChunk = currentChunks[0].idx
        const lastLoadedChunk = currentChunks[currentChunks.length - 1].idx

        // Start with currently loaded chunks
        let chunksNeeded = currentChunks.map((c) => c.idx)

        // Load next chunk if scrolled past 80% and there's more chunks
        if (scrollPct > 0.8 && lastLoadedChunk < article.chunks_meta.length - 1) {
          if (!chunksNeeded.includes(lastLoadedChunk + 1)) {
            chunksNeeded.push(lastLoadedChunk + 1)
          }
          // Drop first chunk if we now have more than 2 chunks (keep sliding window of 2)
          if (chunksNeeded.length > 2) {
            chunksNeeded = chunksNeeded.slice(1)
          }
        }

        // Edge case: if at absolute top and not at first chunk, load previous
        if (container.scrollTop === 0 && firstLoadedChunk > 0) {
          if (!chunksNeeded.includes(firstLoadedChunk - 1)) {
            chunksNeeded.unshift(firstLoadedChunk - 1)
          }
          // Drop last chunk if we now have more than 2 chunks
          if (chunksNeeded.length > 2) {
            chunksNeeded = chunksNeeded.slice(0, -1)
          }
        }
        // Load previous chunk if scrolled below 20% and there's earlier chunks
        else if (scrollPct < 0.2 && firstLoadedChunk > 0) {
          if (!chunksNeeded.includes(firstLoadedChunk - 1)) {
            chunksNeeded.unshift(firstLoadedChunk - 1)
          }
          // Drop last chunk if we now have more than 2 chunks
          if (chunksNeeded.length > 2) {
            chunksNeeded = chunksNeeded.slice(0, -1)
          }
        }

        const neededSet = new Set(chunksNeeded)
        const currentSet = new Set(currentChunks.map((c) => c.idx))

        // Check if chunk set needs updating
        const needsUpdate =
          chunksNeeded.some((idx) => !currentSet.has(idx)) ||
          Array.from(currentSet).some((idx) => !neededSet.has(idx))

        if (needsUpdate) {
          loadChunks(chunksNeeded) // No await - serializes internally
        }
      })
    }

    container.addEventListener('scroll', handleScroll, { passive: true })
    return () => {
      container.removeEventListener('scroll', handleScroll)
      if (rafId) cancelAnimationFrame(rafId)
    }
  }, [article, loadChunks, contentRef])

  // External API: Load chunks, wait for ready, scroll - returns Promise when DONE
  const jumpToPosition = useCallback(
    async ({ chunk, offset }) => {
      // Suspend automatic windowing
      isJumpingRef.current = true

      try {
        const chunksNeeded = getChunksToLoad(chunk, offset)

        // 1. Load chunks (position maintenance disabled during jump)
        await loadChunks(chunksNeeded)

        // 2. Wait for text nodes to be indexed
        await waitForReady(chunk)

        // 3. Scroll
        contentRef.current?.scrollToPosition?.({ chunk, offset, behavior: 'auto' })

        // Promise resolves here - everything is done
      } finally {
        // Resume automatic windowing
        isJumpingRef.current = false
      }
    },
    [loadChunks, waitForReady, getChunksToLoad, contentRef],
  )

  return {
    chunks: Object.values(chunks).sort((a, b) => a.idx - b.idx),
    jumpToPosition,
  }
}
