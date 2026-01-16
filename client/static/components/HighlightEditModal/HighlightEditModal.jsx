import { useState, useRef, useMemo, useEffect } from 'preact/hooks'
import alert from '../../services/alertService'
import Modal from '../Modal/Modal'
import Button from '../Button/Button'
import Icon from '../Icon/Icon'
import Badge from '../Badge/Badge'
import Combobox from '../Combobox/Combobox'
import QuillEditor from '../QuillEditor/QuillEditor'
import { api } from '../../services/api'
import { ROUTES } from '../../services/routes'
import './HighlightEditModal.css'

export default function HighlightEditModal({ highlight, allTags, isOpen, onClose, onSave }) {
  const [loading, setLoading] = useState(true)
  const [fullHighlight, setFullHighlight] = useState(null)
  const [text, setText] = useState('')
  const [prompt, setPrompt] = useState('')
  const [note, setNote] = useState('')
  const [source, setSource] = useState('')
  const [selectedTagIds, setSelectedTagIds] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const textRef = useRef(null)
  const promptRef = useRef(null)
  const noteRef = useRef(null)
  const formRef = useRef(null)

  // Fetch full highlight data when modal opens
  useEffect(() => {
    if (!isOpen || !highlight?.id) return

    const fetchHighlight = async () => {
      setLoading(true)
      try {
        const { data: response } = await api.get(ROUTES.API.highlight(highlight.uuid))
        const data = response.highlight
        setFullHighlight(data)
        setText(data.text || '')
        setPrompt(data.prompt || '')
        setNote(data.note || '')
        setSource(data.source || '')
        setSelectedTagIds(data.tags?.map((t) => t.id) || [])
      } catch (err) {
        console.error('Error fetching highlight:', err)
        setError('Failed to load highlight details.')
      } finally {
        setLoading(false)
      }
    }

    fetchHighlight()
  }, [isOpen, highlight])

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

  const handleSave = async () => {
    setSaving(true)
    setError(null)

    try {
      const data = {
        text: textRef.current?.root.innerHTML || text,
        prompt: promptRef.current?.root.innerHTML || prompt,
        source,
        note: noteRef.current?.root.innerHTML || note,
        tags: selectedTagIds,
      }

      const { data: response } = await api.patch(ROUTES.API.highlight(highlight.uuid), data)
      onSave?.(response.highlight)
      alert.success('Highlight updated')
      onClose()
    } catch (err) {
      console.error('Error saving highlight:', err)
      alert.error('Failed to save changes')
      setError('Failed to save changes. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const handleArchive = async () => {
    setSaving(true)
    setError(null)

    try {
      const { data: response } = await api.delete(ROUTES.API.highlight(highlight.uuid))
      onSave?.(response.highlight)
      alert.success('Highlight archived')
      onClose()
    } catch (err) {
      console.error('Error archiving highlight:', err)
      alert.error(`Failed to archive highlight`)
      setError(`Failed to archive highlight. Please try again.`)
    } finally {
      setSaving(false)
    }
  }

  const handleViewInArticle = () => {
    const articleUuid = fullHighlight?.article_uuid || highlight?.article_uuid
    if (articleUuid) {
      window.location.href = ROUTES.PAGES.reader(articleUuid, highlight.uuid)
    }
  }

  const isArchived = fullHighlight?.archived || highlight?.archived
  const hasArticle = fullHighlight?.article_uuid || highlight?.article_uuid

  const footer = (
    <>
      <Button
        variant="ghost"
        onClick={handleArchive}
        disabled={saving || loading}
        className='archive-btn'
      >
        <Icon name='archive' />
        'Archive'
      </Button>
      <div className="footer-spacer" />
      <Button variant="outline" onClick={onClose} disabled={saving}>
        Cancel
      </Button>
      <Button variant="default" onClick={handleSave} disabled={saving || loading}>
        {saving ? 'Saving...' : 'Save changes'}
      </Button>
      {hasArticle && (
        <Button variant="primary" onClick={handleViewInArticle}>
          <Icon name="visibility" />
          View in article
        </Button>
      )}
    </>
  )

  if (!highlight) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Edit Highlight" size="lg" footer={footer}>
      <div ref={formRef} className="highlight-edit-form">
        {error && <div className="error-banner">{error}</div>}

        {isArchived && !loading && (
          <div className="archived-banner">
            <Icon name="archive" />
            This highlight is archived
          </div>
        )}

        {loading ? (
          <div className="loading-state">Loading highlight details...</div>
        ) : (
          <>
            {/* Article info (read-only) */}
            {fullHighlight?.article_title && (
              <div className="form-group">
                <span className="form-label">From Article</span>
                <div className="article-info">{fullHighlight.article_title}</div>
              </div>
            )}

            {/* Highlight Text (Content) */}
            <div className="form-group">
              <span className="form-label">Content</span>
              <QuillEditor
                ref={textRef}
                defaultValue={text}
                placeholder="Highlight text..."
                className="editor-content"
                boundsRef={formRef}
              />
            </div>

            {/* Prompt */}
            <div className="form-group">
              <span className="form-label">Prompt</span>
              <QuillEditor
                ref={promptRef}
                defaultValue={prompt}
                placeholder="Review prompt..."
                className="editor-prompt"
                boundsRef={formRef}
              />
            </div>

            {/* Source */}
            <div className="form-group">
              <label htmlFor="highlight-source">Source</label>
              <input
                id="highlight-source"
                type="text"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                placeholder="Source (e.g., page number, chapter)"
              />
            </div>

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

            {/* Note */}
            <div className="form-group">
              <span className="form-label">Note</span>
              <QuillEditor
                ref={noteRef}
                defaultValue={note}
                placeholder="Add a note about this highlight..."
                className="editor-note"
                boundsRef={formRef}
              />
            </div>
          </>
        )}
      </div>
    </Modal>
  )
}
