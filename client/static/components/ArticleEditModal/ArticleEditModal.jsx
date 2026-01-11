import { useState, useRef, useMemo, useEffect } from 'preact/hooks'
import alert from '../../services/alertService'
import Modal from '../Modal/Modal'
import Button from '../Button/Button'
import Icon from '../Icon/Icon'
import Badge from '../Badge/Badge'
import Select from '../Select/Select'
import Combobox from '../Combobox/Combobox'
import Progress from '../Progress/Progress'
import QuillEditor from '../QuillEditor/QuillEditor'
import { api } from '../../services/api'
import { ROUTES } from '../../services/routes'
import './ArticleEditModal.css'

const STATUS_OPTIONS = [
  { value: 'in_progress', label: 'In Progress' },
  { value: 'unread', label: 'Unread' },
  { value: 'done', label: 'Done' },
]

function getArticleStatus(article) {
  if (article?.done) return 'done'
  if (article?.unread) return 'unread'
  return 'in_progress'
}

export default function ArticleEditModal({ article, allTags, isOpen, onClose, onSave }) {
  const [loading, setLoading] = useState(true)
  const [fullArticle, setFullArticle] = useState(null)
  const [title, setTitle] = useState('')
  const [status, setStatus] = useState('in_progress')
  const [notes, setNotes] = useState('')
  const [reflections, setReflections] = useState('')
  const [content, setContent] = useState('')
  const [selectedTagIds, setSelectedTagIds] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const notesRef = useRef(null)
  const reflectionsRef = useRef(null)
  const contentRef = useRef(null)
  const formRef = useRef(null)

  // Fetch full article data when modal opens
  useEffect(() => {
    if (!isOpen || !article?.id) return

    const fetchArticle = async () => {
      setLoading(true)
      try {
        const needsContent = article.filetype === 'manual' || article.filetype === 'email'
        const params = needsContent ? { with_content: true } : {}
        const { data: response } = await api.get(ROUTES.API.article(article.id), params)
        const data = response.article
        setFullArticle(data)
        setTitle(data.title || '')
        setStatus(getArticleStatus(data))
        setNotes(data.notes || '')
        setReflections(data.reflections || '')
        setContent(data.content || '')
        setSelectedTagIds(data.tags?.map((t) => t.id) || [])
      } catch (err) {
        console.error('Error fetching article:', err)
        setError('Failed to load article details.')
      } finally {
        setLoading(false)
      }
    }

    fetchArticle()
  }, [isOpen, article?.id])

  const isManualOrEmail = fullArticle?.filetype === 'manual' || fullArticle?.filetype === 'email'
  const showReflections = fullArticle?.done || fullArticle?.reflections
  const progress = Math.round(fullArticle?.progress || article?.progress || 0)

  const tagOptions = useMemo(
    () =>
      allTags.map((tag) => ({
        value: tag.id,
        label: tag.name,
      })),
    [allTags],
  )

  const selectedTagObjects = useMemo(
    () => allTags.filter((tag) => selectedTagIds.includes(tag.id)),
    [allTags, selectedTagIds],
  )

  const handleTagToggle = (tagId) => {
    setSelectedTagIds((prev) =>
      prev.includes(tagId) ? prev.filter((id) => id !== tagId) : [...prev, tagId],
    )
  }

  const copySourceUrl = async () => {
    const url = fullArticle?.source_url || article?.source_url
    if (url) {
      try {
        await navigator.clipboard.writeText(url)
      } catch (err) {
        console.error('Failed to copy:', err)
      }
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)

    try {
      const data = {
        title,
        notes: notesRef.current?.root.innerHTML || notes,
        tags: selectedTagIds,
      }

      if (showReflections) {
        data.reflections = reflectionsRef.current?.root.innerHTML || reflections
      }

      if (isManualOrEmail) {
        data.content = contentRef.current?.root.innerHTML || content
      }

      // Set status flags
      if (status === 'done') {
        data.done = true
        data.unread = false
      } else if (status === 'unread') {
        data.done = false
        data.unread = true
      } else {
        // in_progress
        data.done = false
        data.unread = false
      }

      const { data: response } = await api.patch(ROUTES.API.article(article.id), data)
      onSave?.(response.article)
      alert.success('Article updated')
      onClose()
    } catch (err) {
      console.error('Error saving article:', err)
      alert.error('Failed to save changes')
      setError('Failed to save changes. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const handleArchiveToggle = async () => {
    setSaving(true)
    setError(null)

    const isArchived = fullArticle?.archived || article?.archived
    try {
      const { data: response } = await api.patch(ROUTES.API.article(article.id), {
        archived: !isArchived,
      })
      onSave?.(response.article)
      alert.success(isArchived ? 'Article unarchived' : 'Article archived')
      onClose()
    } catch (err) {
      console.error('Error updating archive status:', err)
      alert.error(`Failed to ${isArchived ? 'unarchive' : 'archive'} article`)
      setError(`Failed to ${isArchived ? 'unarchive' : 'archive'} article. Please try again.`)
    } finally {
      setSaving(false)
    }
  }

  const isArchived = fullArticle?.archived || article?.archived

  const handleStartReading = () => {
    window.location.href = ROUTES.PAGES.article(article.id)
  }

  const footer = (
    <>
      <Button
        variant="ghost"
        onClick={handleArchiveToggle}
        disabled={saving || loading}
        className={isArchived ? 'unarchive-btn' : 'archive-btn'}
      >
        <Icon name={isArchived ? 'unarchive' : 'archive'} />
        {isArchived ? 'Unarchive' : 'Archive'}
      </Button>
      <div className="footer-spacer" />
      <Button variant="outline" onClick={onClose} disabled={saving}>
        Cancel
      </Button>
      <Button variant="default" onClick={handleSave} disabled={saving || loading}>
        {saving ? 'Saving...' : 'Save changes'}
      </Button>
      <Button variant="primary" onClick={handleStartReading}>
        <Icon name="visibility" />
        Start reading
      </Button>
    </>
  )

  if (!article) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Edit Article" size="lg" footer={footer}>
      <div ref={formRef} className="article-edit-form">
        {error && <div className="error-banner">{error}</div>}

        {isArchived && !loading && (
          <div className="archived-banner">
            <Icon name="archive" />
            This article is archived
          </div>
        )}

        {loading ? (
          <div className="loading-state">Loading article details...</div>
        ) : (
          <>
            {/* Title */}
            <div className="form-group">
              <label htmlFor="article-title">Title</label>
              <input
                id="article-title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Article title"
              />
            </div>

            {/* Progress / Status */}
            <div className="form-row">
              <div className="form-group form-group-half">
                <span className="form-label">Progress</span>
                <div className="progress-display">
                  <Progress value={progress} className="edit-progress-bar" />
                  <span className="progress-text">{progress}% complete</span>
                </div>
              </div>
              <div className="form-group form-group-half">
                <label htmlFor="article-status">Status</label>
                <Select
                  id="article-status"
                  options={STATUS_OPTIONS}
                  value={status}
                  onChange={setStatus}
                />
              </div>
            </div>

            {/* Source */}
            {(fullArticle?.source_url || fullArticle?.source) && (
              <div className="form-group">
                <span className="form-label">Source</span>
                <div className="source-display">
                  {fullArticle.source_url ? (
                    <>
                      <a
                        href={fullArticle.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="source-link"
                      >
                        {fullArticle.source_url}
                      </a>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={copySourceUrl}
                        className="copy-btn"
                      >
                        <Icon name="content_copy" />
                      </Button>
                    </>
                  ) : (
                    <span>{fullArticle.source}</span>
                  )}
                </div>
              </div>
            )}

            {/* Tags */}
            <div className="form-group">
              <span className="form-label">Tags</span>
              <Combobox
                options={tagOptions}
                selected={selectedTagIds}
                onSelect={handleTagToggle}
                placeholder="Select tags..."
              />
              {selectedTagObjects.length > 0 && (
                <div className="selected-tags">
                  {selectedTagObjects.map((tag) => (
                    <Badge
                      key={tag.id}
                      variant="outline"
                      value={tag.name}
                      onClick={() => handleTagToggle(tag.id)}
                    >
                      {tag.name}
                      <Icon name="close" className="tag-remove" />
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            {/* Notes */}
            <div className="form-group">
              <span className="form-label">Notes</span>
              <QuillEditor
                ref={notesRef}
                defaultValue={notes}
                placeholder="Add notes about this article..."
                className="editor-notes"
                boundsRef={formRef}
              />
            </div>

            {/* Reflections (only shown for done articles or articles with reflections) */}
            {showReflections && (
              <div className="form-group">
                <span className="form-label">Reflections</span>
                <QuillEditor
                  ref={reflectionsRef}
                  defaultValue={reflections}
                  placeholder="What did you learn from this article?"
                  className="editor-reflections"
                  boundsRef={formRef}
                />
              </div>
            )}

            {/* Content (only for manual/email articles) */}
            {isManualOrEmail && (
              <div className="form-group">
                <span className="form-label">Content</span>
                <QuillEditor
                  ref={contentRef}
                  defaultValue={content}
                  placeholder="Article content..."
                  className="editor-content"
                  boundsRef={formRef}
                  modules={{
                    toolbar: [
                      [{ header: [1, 2, 3, false] }],
                      ['bold', 'italic', 'underline', 'strike'],
                      ['blockquote', 'code-block'],
                      [{ list: 'ordered' }, { list: 'bullet' }],
                      ['link', 'image'],
                      ['clean'],
                    ],
                  }}
                />
              </div>
            )}
          </>
        )}
      </div>
    </Modal>
  )
}
