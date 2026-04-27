import { useState, useRef, useMemo } from 'preact/hooks'
import alert from '../../services/alertService'
import Modal from '../Modal/Modal'
import Button from '../Button/Button'
import Icon from '../Icon/Icon'
import Badge from '../Badge/Badge'
import Combobox from '../Combobox/Combobox'
import QuillEditor from '../QuillEditor/QuillEditor'
import { api } from '../../services/api'
import { ROUTES } from '../../services/routes'
import './HighlightAddModal.css'

export default function HighlightAddModal({
  isOpen,
  onClose,
  selectionData,
  articleUuid,
  allTags = [],
  onSave,
  onTagCreate,
}) {
  const [selectedTagIds, setSelectedTagIds] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [appearsInReviews, setAppearsInReviews] = useState(true)
  const [autogeneratePrompt, setAutogeneratePrompt] = useState(true)

  const noteRef = useRef(null)
  const promptRef = useRef(null)
  const formRef = useRef(null)

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

  const handleTagCreate = async (name) => {
    try {
      const { data } = await api.post(ROUTES.API.TAGS, { name })
      const newTag = data.tag
      onTagCreate?.(newTag)
      setSelectedTagIds((prev) => [...prev, newTag.id])
    } catch (err) {
      console.error('Error creating tag:', err)
      alert.error('Failed to create tag')
    }
  }

  const handleSave = async () => {
    if (!selectionData) return

    setSaving(true)
    setError(null)

    try {
      const data = {
        text: selectionData.text,
        start_chunk: selectionData.start_chunk,
        start: selectionData.start,
        end_chunk: selectionData.end_chunk,
        end: selectionData.end,
        article_uuid: articleUuid,
        note: noteRef.current?.root.innerHTML || '',
        tag_ids: selectedTagIds,
        do_not_review: !appearsInReviews,
        autogenerate_prompt: autogeneratePrompt,
      }

      if (!autogeneratePrompt) {
        data.prompt = promptRef.current?.root.innerHTML || ''
      }

      const { data: response } = await api.post(ROUTES.API.HIGHLIGHTS, data)
      onSave?.(response.highlight)
      alert.success('Highlight created')
      handleClose()
    } catch (err) {
      console.error('Error creating highlight:', err)
      alert.error('Failed to create highlight')
      setError('Failed to create highlight. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const handleClose = () => {
    setSelectedTagIds([])
    setError(null)
    setAppearsInReviews(true)
    setAutogeneratePrompt(true)
    onClose()
  }

  const footer = (
    <>
      <Button variant="outline" onClick={handleClose} disabled={saving}>
        Cancel
      </Button>
      <Button variant="default" onClick={handleSave} disabled={saving || !selectionData}>
        {saving ? 'Creating...' : 'Create highlight'}
      </Button>
    </>
  )

  if (!selectionData) return null

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create Highlight" size="lg" footer={footer}>
      <div ref={formRef} className="highlight-add-form">
        {error && <div className="error-banner">{error}</div>}

        {/* Selected text (read-only) */}
        <div className="form-group">
          <span className="form-label">Selected Text</span>
          <div className="selected-text">{selectionData.text}</div>
        </div>

        {/* Tags */}
        <div className="form-group">
          <span className="form-label">Tags</span>
          <Combobox
            options={tagOptions}
            selected={selectedTagIds}
            onSelect={handleTagToggle}
            placeholder="Select tags..."
            onCreate={handleTagCreate}
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

        {/* Review options */}
        <div className="form-group toggle-group">
          <label>
            <input
              type="checkbox"
              className="toggle"
              checked={appearsInReviews}
              onChange={(e) => setAppearsInReviews(e.target.checked)}
            />
            <span>Appears in reviews</span>
          </label>
        </div>

        <div className="form-group toggle-group">
          <label>
            <input
              type="checkbox"
              className="toggle"
              checked={autogeneratePrompt}
              onChange={(e) => setAutogeneratePrompt(e.target.checked)}
            />
            <span>Autogenerate review prompt</span>
          </label>

          {!autogeneratePrompt && (
            <QuillEditor
              ref={promptRef}
              placeholder="Enter your custom review prompt..."
              className="editor-prompt"
              boundsRef={formRef}
            />
          )}
        </div>

        {/* Note */}
        <div className="form-group">
          <span className="form-label">Note</span>
          <QuillEditor
            ref={noteRef}
            placeholder="Add a note about this highlight..."
            className="editor-note"
            boundsRef={formRef}
          />
        </div>
      </div>
    </Modal>
  )
}
