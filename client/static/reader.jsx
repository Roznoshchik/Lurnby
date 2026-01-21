import { render } from 'preact'
import { useEffect, useState, useRef, useCallback } from 'preact/hooks'
import alert from './services/alertService'
import './css/globals.css'
import './css/reader.css'
import { Layout } from './components/Layout/Layout'
import { ReaderContent } from './components/ReaderContent/ReaderContent'
import { NotesPanel } from './components/NotesPanel/NotesPanel'
import Button from './components/Button/Button'
import Icon from './components/Icon/Icon'
import RequireAuth from './components/RequireAuth/RequireAuth'
import { AuthProvider } from './contexts/AuthContext/AuthContext'
import { api } from './services/api'

function ReaderPage() {
  const [article, setArticle] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // UI state
  const [notesOpen, setNotesOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)

  // Reader state
  const [progress, setProgress] = useState(0)
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

  // Persist reader settings to localStorage
  useEffect(() => {
    localStorage.setItem('readerSettings', JSON.stringify(readerSettings))
  }, [readerSettings])

  const saveTimeoutRef = useRef(null)
  const contentRef = useRef(null)

  // Extract article UUID from URL
  const articleUuid = window.location.pathname.split('/').pop()

  const fetchArticle = async () => {
    try {
      setLoading(true)
      const { data } = await api.get(`/api/articles/${articleUuid}`, { with_content: 'true' })
      setArticle(data.article)
      setProgress(data.article.progress || 0)
      setError(null)
    } catch (err) {
      console.error('Error fetching article:', err)
      setError('Failed to load article')
    } finally {
      setLoading(false)
    }
  }

  const saveProgress = useCallback(
    (newProgress) => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }

      saveTimeoutRef.current = setTimeout(async () => {
        try {
          await api.patch(`/api/articles/${articleUuid}`, { progress: newProgress })
        } catch (err) {
          console.error('Error saving progress:', err)
        }
      }, 2000)
    },
    [articleUuid],
  )

  useEffect(() => {
    fetchArticle()
  }, [articleUuid])

  // Scroll tracking
  useEffect(() => {
    const container = contentRef.current
    if (!container || loading) return

    const handleScroll = () => {
      const scrollTop = container.scrollTop
      const scrollHeight = container.scrollHeight - container.clientHeight
      const scrollPercent = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0
      const newProgress = Math.min(100, Math.max(0, scrollPercent))

      setProgress(newProgress)
      saveProgress(newProgress)
    }

    container.addEventListener('scroll', handleScroll, { passive: true })
    return () => container.removeEventListener('scroll', handleScroll)
  }, [articleUuid, loading, saveProgress])

  const saveNotes = useCallback(
    async (notes) => {
      try {
        await api.patch(`/api/articles/${articleUuid}`, { notes })
        setArticle((prev) => ({ ...prev, notes }))
      } catch (err) {
        console.error('Error saving notes:', err)
        alert.error('Failed to save notes')
      }
    },
    [articleUuid],
  )

  // Line height SVG icons
  const LineHeightIcon = ({ spacing }) => {
    const positions = {
      min: [0, 5, 10],
      mid: [0, 8, 16],
      max: [0, 11, 22],
    }
    const y = positions[spacing]
    return (
      <svg xmlns="http://www.w3.org/2000/svg" width="38" height="24" viewBox="0 0 38 24" fill="currentColor">
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

  // Sidebar content for reader - render prop receives isExpanded
  const sidebarContent = ({ isExpanded }) => (
    <>
      <button
        type="button"
        onClick={() => {
          setNotesOpen(!notesOpen)
          setSettingsOpen(false)
        }}
        className={`nav-link ${!isExpanded ? 'centered' : ''} ${notesOpen ? 'active' : ''}`}
        title={!isExpanded ? 'Notes' : undefined}
      >
        <Icon name="edit_note" className="icon" />
        {isExpanded && <span>Notes</span>}
      </button>

      <div style={{ position: 'relative' }}>
        <button
          type="button"
          onClick={() => {
            setSettingsOpen(!settingsOpen)
            setNotesOpen(false)
          }}
          className={`nav-link ${!isExpanded ? 'centered' : ''} ${settingsOpen ? 'active' : ''}`}
          title={!isExpanded ? 'Settings' : undefined}
        >
          <Icon name="text_format" className="icon" />
          {isExpanded && <span>Settings</span>}
        </button>

        {settingsOpen && <SettingsPopout />}
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

  return (
    <Layout sidebarContent={sidebarContent}>
      <div className={`reader-wrapper ${notesOpen ? 'with-notes' : ''}`}>
        <ReaderContent ref={contentRef} article={article} progress={progress} settings={readerSettings} />

        {notesOpen && (
          <NotesPanel
            notes={article?.notes || ''}
            onChange={saveNotes}
            onClose={() => setNotesOpen(false)}
          />
        )}
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
