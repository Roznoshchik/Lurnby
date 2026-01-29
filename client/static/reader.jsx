import { render } from 'preact'
import { useEffect, useState, useRef, useCallback } from 'preact/hooks'
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
import RequireAuth from './components/RequireAuth/RequireAuth'
import { AuthProvider } from './contexts/AuthContext/AuthContext'
import { api } from './services/api'
import { ROUTES } from './services/routes'
import { useReaderProgress } from './hooks/useReaderProgress'
import { useReaderBookmarks } from './hooks/useReaderBookmarks'
import { useReaderHighlights } from './hooks/useReaderHighlights'

function ReaderPage() {
  const [article, setArticle] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

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

  const contentRef = useRef(null)
  const bookmarkInputRef = useRef(null)
  const settingsPopoutRef = useRef(null)
  const bookmarksPopoutRef = useRef(null)

  const articleUuid = window.location.pathname.split('/').pop()
  const highlightUuid = new URLSearchParams(window.location.search).get('highlight')

  // Callback for when a highlight is created (used by hook and modal)
  const handleHighlightCreated = useCallback((highlight) => {
    setHighlightModalOpen(false)
    setHighlightSelectionData(null)
    if (highlight) {
      setArticle((prev) => ({
        ...prev,
        highlights: [...(prev.highlights || []), highlight],
      }))
    }
  }, [])

  // Callback for highlight click in reader
  const handleHighlightClick = useCallback(
    (highlightId) => {
      const highlight = article?.highlights?.find((h) => h.uuid === highlightId)
      if (highlight) {
        setEditingHighlight(highlight)
        setEditModalOpen(true)
      }
    },
    [article?.highlights],
  )

  // Callback for highlight update
  const handleHighlightSave = useCallback((updatedHighlight) => {
    setEditModalOpen(false)
    setEditingHighlight(null)
    if (updatedHighlight) {
      setArticle((prev) => ({
        ...prev,
        highlights: prev.highlights.map((h) => (h.uuid === updatedHighlight.uuid ? updatedHighlight : h)),
      }))
    }
  }, [])

  // Callback for highlight removal
  const handleHighlightRemove = useCallback((removedHighlight) => {
    setEditModalOpen(false)
    setEditingHighlight(null)
    if (removedHighlight) {
      setArticle((prev) => ({
        ...prev,
        highlights: prev.highlights.filter((h) => h.uuid !== removedHighlight.uuid),
      }))
    }
  }, [])

  // Hooks
  const { progress } = useReaderProgress(contentRef, articleUuid, loading, article?.progress || 0)

  const {
    addBookmark,
    deleteBookmark,
    jumpToBookmark,
    resetFurthest,
    furthestBookmark,
    userBookmarks,
  } = useReaderBookmarks(
    contentRef,
    articleUuid,
    loading,
    article?.bookmarks,
    setArticle,
  )

  const { popoverOpen, setPopoverOpen, selectionRect, createHighlight, openHighlightModal } =
    useReaderHighlights(contentRef, articleUuid, loading, handleHighlightCreated)

  const fetchArticle = async () => {
    try {
      setLoading(true)
      const { data } = await api.get(ROUTES.API.article(articleUuid), { with_content: 'true' })
      setArticle(data.article)
      setError(null)
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
  const BookmarksPopout = () => (
    <div className="reader-bookmarks-popout">
      <div className="bookmarks-add">
        <input
          ref={bookmarkInputRef}
          type="text"
          placeholder="Bookmark name..."
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
              onClick={() => jumpToBookmark(furthestBookmark)}
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

        {userBookmarks.map((bookmark) => (
          <div key={bookmark.name} className="bookmark-item">
            <button
              type="button"
              className="bookmark-name"
              onClick={() => jumpToBookmark(bookmark)}
            >
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
        <div className="reader-loading">
          <p>Loading article...</p>
        </div>
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
        <ReaderContent
          ref={contentRef}
          article={article}
          progress={progress}
          settings={readerSettings}
          bookmarks={article?.bookmarks || []}
          highlights={article?.highlights || []}
          onHighlightClick={handleHighlightClick}
          scrollToHighlight={highlightUuid}
        />

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
