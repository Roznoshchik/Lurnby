import { render } from 'preact'
import { useEffect, useState, useRef, useCallback, useMemo } from 'preact/hooks'
import alert from './services/alertService'
import './css/globals.css'
import './css/reader.css'
import { Layout } from './components/Layout/Layout'
import { ReaderContent } from './components/ReaderContent/ReaderContent'
import { NotesPanel } from './components/NotesPanel/NotesPanel'
import HighlightPopover from './components/HighlightPopover/HighlightPopover'
import HighlightAddModal from './components/HighlightAddModal/HighlightAddModal'
import HighlightEditModal from './components/HighlightEditModal/HighlightEditModal'
import Button from './components/Button/Button'
import Icon from './components/Icon/Icon'
import Loader from './components/Loader/Loader'
import RequireAuth from './components/RequireAuth/RequireAuth'
import { AuthProvider } from './contexts/AuthContext/AuthContext'
import { api } from './services/api'
import { ROUTES } from './services/routes'
import { useReaderHighlights } from './hooks/useReaderHighlights'
import { useChunkWindow } from './hooks/useChunkWindow'

// Parse URL params for reader
function getReaderParams() {
  const params = new URLSearchParams(window.location.search)
  return {
    chunk: params.get('chunk') ? parseInt(params.get('chunk'), 10) : 0,
    offset: params.get('offset') ? parseInt(params.get('offset'), 10) : 0,
    unprocessed: params.get('unprocessed') === '1',
    highlight: params.get('highlight'),
  }
}

// Normalize bookmarks to array format (handles legacy object format)
function normalizeBookmarks(bookmarks) {
  let normalized = []

  if (Array.isArray(bookmarks)) {
    normalized = bookmarks
  } else if (bookmarks && typeof bookmarks === 'object') {
    // Legacy format: {furthest: 40.5, "Ch5": 25.2} - ignore for now, will be migrated on backend
    normalized = []
  } else {
    normalized = []
  }

  // Ensure furthest bookmark always exists
  const hasFurthest = normalized.some((b) => b.name === 'furthest')
  if (!hasFurthest) {
    normalized.push({ name: 'furthest', chunk: 0, offset: 0 })
  }

  return normalized
}

function ReaderPage() {
  const [article, setArticle] = useState(null)
  const [loading, setLoading] = useState(true)
  const [chunkLoading, setChunkLoading] = useState(false)
  const [error, setError] = useState(null)

  // State
  const [bookmarks, setBookmarks] = useState([])
  const [highlights, setHighlights] = useState([])
  const [progress, setProgress] = useState(0)

  // UI state
  const [notesOpen, setNotesOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [bookmarksOpen, setBookmarksOpen] = useState(false)
  const [highlightModalOpen, setHighlightModalOpen] = useState(false)
  const [highlightSelectionData, setHighlightSelectionData] = useState(null)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [editingHighlight, setEditingHighlight] = useState(null)

  // Tags for highlight creation
  const [allTags, setAllTags] = useState([])

  // Reader settings
  const [readerSettings, setReaderSettings] = useState(() => {
    const saved = localStorage.getItem('readerSettings')
    if (saved) {
      try {
        return JSON.parse(saved)
      } catch {
        return { font: 'sans-serif', size: 4, spacing: 'line-height-mid' }
      }
    }
    return { font: 'sans-serif', size: 4, spacing: 'line-height-mid' }
  })

  useEffect(() => {
    localStorage.setItem('readerSettings', JSON.stringify(readerSettings))
  }, [readerSettings])

  // Close popouts on outside click
  useEffect(() => {
    if (!settingsOpen && !bookmarksOpen) return

    const handleClickOutside = (e) => {
      if (settingsOpen && settingsPopoutRef.current && !settingsPopoutRef.current.contains(e.target)) {
        setSettingsOpen(false)
      }
      if (bookmarksOpen && bookmarksPopoutRef.current && !bookmarksPopoutRef.current.contains(e.target)) {
        setBookmarksOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [settingsOpen, bookmarksOpen])

  // Focus bookmark input when popout opens
  useEffect(() => {
    if (bookmarksOpen && bookmarkInputRef.current) {
      bookmarkInputRef.current.focus()
    }
  }, [bookmarksOpen])

  // Refs
  const contentRef = useRef(null)
  const bookmarkInputRef = useRef(null)
  const settingsPopoutRef = useRef(null)
  const bookmarksPopoutRef = useRef(null)

  const articleUuid = window.location.pathname.split('/').pop()
  const urlParams = useMemo(() => getReaderParams(), [])
  const { chunk: initialChunk, offset: initialOffset, unprocessed: isUnprocessed, highlight: highlightUuid } = urlParams

  // Callback for when highlights are loaded with chunks
  const handleHighlightsLoaded = useCallback((newHighlights) => {
    setHighlights((prev) => {
      const existing = new Set(prev.map((h) => h.uuid))
      const filtered = newHighlights.filter((h) => !existing.has(h.uuid))
      return [...prev, ...filtered]
    })
  }, [])

  // Use chunk window hook for automatic chunk management
  const { chunks, jumpToPosition } = useChunkWindow({
    contentRef,
    articleUuid,
    article,
    onHighlightsLoaded: handleHighlightsLoaded,
  })

  // Jump to bookmark using hook
  const handleJumpToBookmark = useCallback(
    async (bookmark) => {
      if (bookmark.chunk == null || bookmark.offset == null) return
      setChunkLoading(true)
      try {
        await jumpToPosition({ chunk: bookmark.chunk, offset: bookmark.offset })
      } finally {
        setChunkLoading(false)
      }
    },
    [jumpToPosition],
  )

  // Callback for when a highlight is created (used by hook and modal)
  const handleHighlightCreated = useCallback((highlight) => {
    setHighlightModalOpen(false)
    setHighlightSelectionData(null)
    if (highlight) {
      setHighlights((prev) => [...prev, highlight])
    }
  }, [])

  // Callback for highlight click in reader
  const handleHighlightClick = useCallback(
    (highlightId) => {
      const highlight = highlights.find((h) => h.uuid === highlightId)
      if (highlight) {
        setEditingHighlight(highlight)
        setEditModalOpen(true)
      }
    },
    [highlights],
  )

  // Callback for highlight update
  const handleHighlightSave = useCallback((updatedHighlight) => {
    setEditModalOpen(false)
    setEditingHighlight(null)
    if (updatedHighlight) {
      setHighlights((prev) =>
        prev.map((h) => (h.uuid === updatedHighlight.uuid ? updatedHighlight : h)),
      )
    }
  }, [])

  // Callback for highlight removal
  const handleHighlightRemove = useCallback((removedHighlight) => {
    setEditModalOpen(false)
    setEditingHighlight(null)
    if (removedHighlight) {
      setHighlights((prev) => prev.filter((h) => h.uuid !== removedHighlight.uuid))
    }
  }, [])

  // Derive bookmark lists from state
  const furthestBookmark = useMemo(
    () => bookmarks.find((b) => b.name === 'furthest'),
    [bookmarks],
  )
  const userBookmarks = useMemo(
    () => bookmarks.filter((b) => b.name !== 'furthest'),
    [bookmarks],
  )

  // Bookmark CRUD operations
  const addBookmark = useCallback(
    async (name) => {
      if (!name?.trim()) return false
      const position = contentRef.current?.getReaderLocation()
      if (!position) return false

      try {
        const newBookmark = { name: name.trim(), chunk: position.chunk, offset: position.offset }
        const updatedBookmarks = [...bookmarks, newBookmark]
        await api.patch(ROUTES.API.article(articleUuid), { bookmarks: updatedBookmarks })
        setBookmarks(updatedBookmarks)
        return true
      } catch (err) {
        console.error('Error adding bookmark:', err)
        alert.error('Failed to add bookmark')
        return false
      }
    },
    [articleUuid, bookmarks],
  )

  const deleteBookmark = useCallback(
    async (name) => {
      try {
        const updatedBookmarks = bookmarks.filter((b) => b.name !== name)
        await api.patch(ROUTES.API.article(articleUuid), { bookmarks: updatedBookmarks })
        setBookmarks(updatedBookmarks)
      } catch (err) {
        console.error('Error deleting bookmark:', err)
        alert.error('Failed to delete bookmark')
      }
    },
    [articleUuid, bookmarks],
  )

  const resetFurthest = useCallback(async () => {
    const position = contentRef.current?.getReaderLocation()
    if (!position) return

    try {
      const updatedBookmarks = bookmarks.map((b) =>
        b.name === 'furthest' ? { ...b, chunk: position.chunk, offset: position.offset } : b,
      )
      await api.patch(ROUTES.API.article(articleUuid), { bookmarks: updatedBookmarks })
      setBookmarks(updatedBookmarks)
    } catch (err) {
      console.error('Error resetting furthest:', err)
      alert.error('Failed to reset furthest')
    }
  }, [articleUuid, bookmarks])

  const reorderBookmarks = useCallback(
    async (reorderedUserBookmarks) => {
      try {
        // Combine furthest bookmark with reordered user bookmarks
        const updatedBookmarks = [furthestBookmark, ...reorderedUserBookmarks].filter(Boolean)
        await api.patch(ROUTES.API.article(articleUuid), { bookmarks: updatedBookmarks })
        setBookmarks(updatedBookmarks)
      } catch (err) {
        console.error('Error reordering bookmarks:', err)
        alert.error('Failed to reorder bookmarks')
      }
    },
    [articleUuid, furthestBookmark],
  )

  const { popoverOpen, setPopoverOpen, selectionRect, createHighlight, openHighlightModal } =
    useReaderHighlights(contentRef, articleUuid, loading, handleHighlightCreated)

  // Ref for initial position to navigate to after article loads
  const initialPositionRef = useRef(null)
  const hasJumpedRef = useRef(false)

  const fetchArticle = async () => {
    try {
      setLoading(true)
      hasJumpedRef.current = false

      if (isUnprocessed) {
        setChunkLoading(true)
        const params = highlightUuid ? { highlight: highlightUuid } : {}
        const { data } = await api.post(ROUTES.API.articleProcess(articleUuid), null, params)

        setArticle(data.article)
        const normalizedBookmarks = normalizeBookmarks(data.article.bookmarks)
        setBookmarks(normalizedBookmarks)
        setHighlights(data.highlights || [])

        let scrollPosition = { chunk: data.position.chunk, offset: data.position.offset }
        if (!highlightUuid) {
          const furthest = normalizedBookmarks.find((b) => b.name === 'furthest')
          if (furthest && furthest.chunk != null && furthest.offset != null) {
            scrollPosition = { chunk: furthest.chunk, offset: furthest.offset }
          }
        }

        const newUrl = ROUTES.PAGES.reader(articleUuid, scrollPosition)
        window.history.replaceState({}, '', newUrl)
        initialPositionRef.current = scrollPosition
      } else {
        const { data } = await api.get(ROUTES.API.article(articleUuid))
        const normalizedBookmarks = normalizeBookmarks(data.article.bookmarks)

        setArticle(data.article)
        setBookmarks(normalizedBookmarks)

        let scrollPosition = { chunk: initialChunk, offset: initialOffset }
        if (highlightUuid) {
          const highlight = data.article.highlights?.find((h) => h.uuid === highlightUuid)
          if (highlight?.start_chunk != null) {
            scrollPosition = { chunk: highlight.start_chunk, offset: highlight.start || 0 }
          }
        }
        initialPositionRef.current = scrollPosition
      }

      setError(null)
      api.patch(ROUTES.API.article(articleUuid), {
        date_read: new Date().toISOString(),
        unread: false,
      }).catch(() => {})
    } catch (err) {
      console.error('Error fetching article:', err)
      setError('Failed to load article')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchArticle()
  }, [articleUuid])

  // Initial jump after article loads - hook handles chunk loading + text node indexing + scroll
  useEffect(() => {
    if (loading || !article || hasJumpedRef.current || !initialPositionRef.current) return

    hasJumpedRef.current = true
    const position = initialPositionRef.current
    initialPositionRef.current = null

    jumpToPosition(position).finally(() => setChunkLoading(false))
  }, [loading, article, jumpToPosition])

  // Mirror chunks in a ref for use in scroll handler (avoids stale closure)
  const chunksForProgressRef = useRef([])
  useEffect(() => {
    chunksForProgressRef.current = chunks
  }, [chunks])

  // Progress tracking via scroll
  useEffect(() => {
    if (loading || !article?.chunks_meta) return

    const container = contentRef.current?.contentContainer
    if (!container) return

    let rafId = null

    const handleScroll = () => {
      if (rafId) return
      rafId = requestAnimationFrame(() => {
        rafId = null

        const currentChunks = chunksForProgressRef.current
        if (currentChunks.length === 0) return

        const scrollableHeight = container.scrollHeight - container.clientHeight

        if (scrollableHeight <= 0) {
          const lastChunk = currentChunks[currentChunks.length - 1]
          if (lastChunk.idx === article.chunks_meta.length - 1) {
            setProgress(100)
          } else {
            const loadedEnd = article.chunks_meta
              .slice(0, lastChunk.idx + 1)
              .reduce((sum, c) => sum + c.text_length, 0)
            setProgress((loadedEnd / article.total_length) * 100)
          }
        } else {
          const scrollPct = container.scrollTop / scrollableHeight
          const firstChunk = currentChunks[0]
          const loadedTextLength = currentChunks.reduce((sum, c) => sum + c.text_length, 0)
          const offsetInLoaded = scrollPct * loadedTextLength

          let cumulativeLength = 0
          let currentChunkIdx = firstChunk.idx
          let currentOffset = 0

          for (const chunk of currentChunks) {
            if (offsetInLoaded <= cumulativeLength + chunk.text_length) {
              currentChunkIdx = chunk.idx
              currentOffset = offsetInLoaded - cumulativeLength
              break
            }
            cumulativeLength += chunk.text_length
          }

          if (offsetInLoaded > loadedTextLength) {
            const lastChunk = currentChunks[currentChunks.length - 1]
            currentChunkIdx = lastChunk.idx
            currentOffset = lastChunk.text_length
          }

          const articlePos =
            article.chunks_meta.slice(0, currentChunkIdx).reduce((sum, c) => sum + c.text_length, 0) + currentOffset
          setProgress(Math.min(100, Math.max(0, (articlePos / article.total_length) * 100)))
        }
      })
    }

    container.addEventListener('scroll', handleScroll, { passive: true })
    handleScroll()

    return () => {
      container.removeEventListener('scroll', handleScroll)
      if (rafId) cancelAnimationFrame(rafId)
    }
  }, [loading, article])

  // Debounced progress saving + furthest bookmark update
  const savedProgressRef = useRef(0)
  useEffect(() => {
    if (loading || progress <= savedProgressRef.current) return

    const timeout = setTimeout(async () => {
      // Get position at top of viewport for furthest tracking
      const position = contentRef.current?.getReaderLocation('top')
      if (!position) return

      try {
        // Only update furthest if current position is further than saved
        const currentFurthest = bookmarks.find((b) => b.name === 'furthest')
        const isFurther = !currentFurthest ||
          position.chunk > currentFurthest.chunk ||
          (position.chunk === currentFurthest.chunk && position.offset > currentFurthest.offset)

        const updates = { progress }
        if (isFurther) {
          const updatedBookmarks = bookmarks.map((b) =>
            b.name === 'furthest' ? { ...b, chunk: position.chunk, offset: position.offset } : b,
          )
          updates.bookmarks = updatedBookmarks
          setBookmarks(updatedBookmarks)
        }

        if (progress >= 100) updates.done = true

        await api.patch(ROUTES.API.article(articleUuid), updates)
        savedProgressRef.current = progress
      } catch (err) {
        console.error('Error saving progress:', err)
      }
    }, 2000)

    return () => clearTimeout(timeout)
  }, [loading, progress, articleUuid, bookmarks])

  // Fetch tags for highlight creation modal
  useEffect(() => {
    const fetchTags = async () => {
      try {
        const { data } = await api.get(ROUTES.API.TAGS)
        setAllTags(data.tags || [])
      } catch (err) {
        console.error('Error fetching tags:', err)
      }
    }
    fetchTags()
  }, [])

  const saveNotes = useCallback(
    async (notes) => {
      try {
        await api.patch(ROUTES.API.article(articleUuid), { notes })
        setArticle((prev) => ({ ...prev, notes }))
      } catch (err) {
        console.error('Error saving notes:', err)
        alert.error('Failed to save notes')
      }
    },
    [articleUuid],
  )

  const handleAddBookmark = () => {
    const name = bookmarkInputRef.current?.value?.trim()
    if (addBookmark(name)) {
      bookmarkInputRef.current.value = ''
    }
  }

  const handleOpenHighlightModal = () => {
    const data = openHighlightModal()
    if (data) {
      setHighlightSelectionData(data)
      setHighlightModalOpen(true)
    }
  }

  const handleTagCreate = (newTag) => {
    setAllTags((prev) => [...prev, newTag])
  }

  // Line height SVG icons
  const LineHeightIcon = ({ spacing }) => {
    const positions = {
      min: [0, 5, 10],
      mid: [0, 8, 16],
      max: [0, 11, 22],
    }
    const y = positions[spacing]
    return (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="38"
        height="24"
        viewBox="0 0 38 24"
        fill="currentColor"
        role="img"
        aria-label="Line spacing"
      >
        <rect x="0" y={y[0]} width="28" height="2" />
        <rect x="0" y={y[1]} width="38" height="2" />
        <rect x="0" y={y[2]} width="18" height="2" />
      </svg>
    )
  }

  // Settings popout component
  const SettingsPopout = () => (
    <div className="reader-settings-popout">
      <div className="settings-group">
        <div className="settings-buttons font-buttons">
          <button
            type="button"
            className={`settings-btn font-btn sans-serif ${readerSettings.font === 'sans-serif' ? 'active' : ''}`}
            onClick={() => setReaderSettings((s) => ({ ...s, font: 'sans-serif' }))}
          >
            <span className="font-label">Sans-serif</span>
            <span className="font-preview">Aa</span>
          </button>
          <button
            type="button"
            className={`settings-btn font-btn serif ${readerSettings.font === 'serif' ? 'active' : ''}`}
            onClick={() => setReaderSettings((s) => ({ ...s, font: 'serif' }))}
          >
            <span className="font-label">Serif</span>
            <span className="font-preview">Aa</span>
          </button>
        </div>
      </div>

      <div className="settings-group">
        <div className="settings-buttons size-buttons">
          <button
            type="button"
            className="settings-btn size-btn"
            onClick={() => setReaderSettings((s) => ({ ...s, size: Math.max(1, s.size - 1) }))}
          >
            -
          </button>
          <span className="settings-value">{readerSettings.size}</span>
          <button
            type="button"
            className="settings-btn size-btn"
            onClick={() => setReaderSettings((s) => ({ ...s, size: Math.min(15, s.size + 1) }))}
          >
            +
          </button>
        </div>
      </div>

      <div className="settings-group">
        <div className="settings-buttons spacing-buttons">
          <button
            type="button"
            className={`settings-btn spacing-btn ${readerSettings.spacing === 'line-height-min' ? 'active' : ''}`}
            onClick={() => setReaderSettings((s) => ({ ...s, spacing: 'line-height-min' }))}
          >
            <LineHeightIcon spacing="min" />
          </button>
          <button
            type="button"
            className={`settings-btn spacing-btn ${readerSettings.spacing === 'line-height-mid' ? 'active' : ''}`}
            onClick={() => setReaderSettings((s) => ({ ...s, spacing: 'line-height-mid' }))}
          >
            <LineHeightIcon spacing="mid" />
          </button>
          <button
            type="button"
            className={`settings-btn spacing-btn ${readerSettings.spacing === 'line-height-max' ? 'active' : ''}`}
            onClick={() => setReaderSettings((s) => ({ ...s, spacing: 'line-height-max' }))}
          >
            <LineHeightIcon spacing="max" />
          </button>
        </div>
      </div>
    </div>
  )

  // Bookmarks popout component
  const BookmarksPopout = () => {
    const [draggedIndex, setDraggedIndex] = useState(null)
    const [dragOverIndex, setDragOverIndex] = useState(null)

    const handleDragStart = (e, index) => {
      setDraggedIndex(index)
      e.dataTransfer.effectAllowed = 'move'
    }

    const handleDragOver = (e, index) => {
      e.preventDefault()
      e.dataTransfer.dropEffect = 'move'
      if (index !== draggedIndex) {
        setDragOverIndex(index)
      }
    }

    const handleDrop = (e, dropIndex) => {
      e.preventDefault()
      if (draggedIndex === null || draggedIndex === dropIndex) {
        setDraggedIndex(null)
        setDragOverIndex(null)
        return
      }

      const reordered = [...userBookmarks]
      const [movedBookmark] = reordered.splice(draggedIndex, 1)
      reordered.splice(dropIndex, 0, movedBookmark)

      reorderBookmarks(reordered)
      setDraggedIndex(null)
      setDragOverIndex(null)
    }

    const handleDragEnd = () => {
      setDraggedIndex(null)
      setDragOverIndex(null)
    }

    return (
      <div className="reader-bookmarks-popout">
        <div className="bookmarks-add">
          <input
            ref={bookmarkInputRef}
            type="text"
            placeholder="Bookmark name..."
            autoFocus
            onKeyDown={(e) => e.key === 'Enter' && handleAddBookmark()}
          />
          <Button variant="default" size="sm" onClick={handleAddBookmark}>
            Add
          </Button>
        </div>

        <div className="bookmarks-list">
          {furthestBookmark && (
            <div className="bookmark-item">
              <button
                type="button"
                className="bookmark-name"
                onClick={() => handleJumpToBookmark(furthestBookmark)}
              >
                Furthest read
              </button>
              <button
                type="button"
                className="bookmark-reset"
                onClick={resetFurthest}
                title="Reset to current position"
              >
                <Icon name="restart_alt" />
              </button>
            </div>
          )}

          {userBookmarks.map((bookmark, index) => (
            <div
              key={bookmark.name}
              className={`bookmark-item ${draggedIndex === index ? 'dragging' : ''} ${dragOverIndex === index ? 'drag-over' : ''}`}
              draggable
              onDragStart={(e) => handleDragStart(e, index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDrop={(e) => handleDrop(e, index)}
              onDragEnd={handleDragEnd}
            >
              <button
                type="button"
                className="bookmark-name"
                onClick={() => handleJumpToBookmark(bookmark)}
              >
                <Icon name="drag_indicator" className="drag-handle" />
                {bookmark.name}
              </button>
              <button
                type="button"
                className="bookmark-delete"
                onClick={() => deleteBookmark(bookmark.name)}
              >
                <Icon name="close" />
              </button>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Sidebar content for reader
  const sidebarContent = ({ isExpanded }) => (
    <>
      <button
        type="button"
        onClick={() => {
          setNotesOpen(!notesOpen)
          setSettingsOpen(false)
          setBookmarksOpen(false)
        }}
        className={`nav-link ${!isExpanded ? 'centered' : ''} ${notesOpen ? 'active' : ''}`}
        title={!isExpanded ? 'Notes' : undefined}
      >
        <Icon name="edit_document" className="icon" />
        {isExpanded && <span>Notes</span>}
      </button>

      <div ref={settingsPopoutRef} className="sidebar-popout-wrapper">
        <button
          type="button"
          onClick={() => {
            setSettingsOpen(!settingsOpen)
            setBookmarksOpen(false)
          }}
          className={`nav-link ${!isExpanded ? 'centered' : ''} ${settingsOpen ? 'active' : ''}`}
          title={!isExpanded ? 'Settings' : undefined}
        >
          <Icon name="serif" className="icon" />
          {isExpanded && <span>Settings</span>}
        </button>

        {settingsOpen && <SettingsPopout />}
      </div>

      <div ref={bookmarksPopoutRef} className="sidebar-popout-wrapper">
        <button
          type="button"
          onClick={() => {
            setBookmarksOpen(!bookmarksOpen)
            setSettingsOpen(false)
          }}
          className={`nav-link ${!isExpanded ? 'centered' : ''} ${bookmarksOpen ? 'active' : ''}`}
          title={!isExpanded ? 'Bookmarks' : undefined}
        >
          <Icon name="bookmarks" className="icon" />
          {isExpanded && <span>Bookmarks</span>}
        </button>

        {bookmarksOpen && <BookmarksPopout />}
      </div>

      {article?.source_url && (
        <button
          type="button"
          onClick={() => window.open(article.source_url, '_blank')}
          className={`nav-link ${!isExpanded ? 'centered' : ''}`}
          title={!isExpanded ? 'View original' : undefined}
        >
          <Icon name="open_in_new" className="icon" />
          {isExpanded && <span>View original</span>}
        </button>
      )}
    </>
  )

  if (loading) {
    return (
      <Layout>
        <Loader isLoading={true} text="Loading article..." />
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout>
        <div className="reader-error">
          <p>{error}</p>
          <Button onClick={fetchArticle}>Retry</Button>
        </div>
      </Layout>
    )
  }

  // Get container ref for popover bounds
  const readerContainerRef = useRef(null)

  return (
    <Layout sidebarContent={sidebarContent}>
      <div ref={readerContainerRef} className={`reader-wrapper ${notesOpen ? 'with-notes' : ''}`}>
        <Loader isLoading={chunkLoading} mode="overlay" text="Loading...">
          <ReaderContent
            ref={contentRef}
            title={article?.title}
            chunks={chunks}
            progress={progress}
            settings={readerSettings}
            bookmarks={bookmarks}
            highlights={highlights}
            onHighlightClick={handleHighlightClick}
          />
        </Loader>

        {notesOpen && (
          <NotesPanel
            notes={article?.notes || ''}
            onChange={saveNotes}
            onClose={() => setNotesOpen(false)}
          />
        )}

        <HighlightPopover
          isOpen={popoverOpen}
          onClose={() => setPopoverOpen(false)}
          anchorRect={selectionRect}
          containerRef={readerContainerRef}
          onHighlight={createHighlight}
          onHighlightWithNotes={handleOpenHighlightModal}
        />

        <HighlightAddModal
          isOpen={highlightModalOpen}
          onClose={() => {
            setHighlightModalOpen(false)
            setHighlightSelectionData(null)
          }}
          selectionData={highlightSelectionData}
          articleUuid={articleUuid}
          allTags={allTags}
          onSave={handleHighlightCreated}
          onTagCreate={handleTagCreate}
        />

        <HighlightEditModal
          isOpen={editModalOpen}
          onClose={() => {
            setEditModalOpen(false)
            setEditingHighlight(null)
          }}
          highlight={editingHighlight}
          allTags={allTags}
          onSave={handleHighlightSave}
          onRemove={handleHighlightRemove}
          onTagCreate={handleTagCreate}
        />
      </div>
    </Layout>
  )
}

function Reader() {
  return (
    <AuthProvider>
      <RequireAuth>
        <ReaderPage />
      </RequireAuth>
    </AuthProvider>
  )
}

render(<Reader />, document.getElementById('app'))
