import { useState, useEffect } from 'preact/hooks'
import alert from '../../services/alertService'
import Modal from '../Modal/Modal'
import Button from '../Button/Button'
import Icon from '../Icon/Icon'
import { api } from '../../services/api'
import { ROUTES } from '../../services/routes'
import './TagEditModal.css'

export default function TagEditModal({ tag, isOpen, onClose, onSave, onDelete }) {
  const [name, setName] = useState('')
  const [archived, setArchived] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const isNew = !tag?.id

  useEffect(() => {
    if (isOpen && tag) {
      setName(tag.name || '')
      setArchived(tag.archived || false)
      setError(null)
    } else if (isOpen && !tag) {
      setName('')
      setArchived(false)
      setError(null)
    }
  }, [isOpen, tag])

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Tag name is required')
      return
    }

    setSaving(true)
    setError(null)

    try {
      let response
      if (isNew) {
        response = await api.post(ROUTES.API.TAGS, { name: name.trim() })
        alert.success('Tag created')
      } else {
        response = await api.patch(`${ROUTES.API.TAGS}/${tag.uuid}`, {
          name: name.trim(),
          archived,
        })
        alert.success('Tag updated')
      }
      onSave?.(response.data.tag)
      onClose()
    } catch (err) {
      console.error('Error saving tag:', err)
      alert.error(isNew ? 'Failed to create tag' : 'Failed to save changes')
      setError('Failed to save. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this tag? This cannot be undone.')) {
      return
    }

    setSaving(true)
    setError(null)

    try {
      await api.delete(`${ROUTES.API.TAGS}/${tag.uuid}`)
      alert.success('Tag deleted')
      onDelete?.(tag)
      onClose()
    } catch (err) {
      console.error('Error deleting tag:', err)
      alert.error('Failed to delete tag')
      setError('Failed to delete tag. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const footer = (
    <>
      {!isNew && (
        <Button
          variant="ghost"
          onClick={handleDelete}
          disabled={saving}
          className="delete-btn"
        >
          <Icon name="delete" />
          Delete
        </Button>
      )}
      <div className="footer-spacer" />
      <Button variant="outline" onClick={onClose} disabled={saving}>
        Cancel
      </Button>
      <Button variant="default" onClick={handleSave} disabled={saving || !name.trim()}>
        {saving ? 'Saving...' : isNew ? 'Create' : 'Save changes'}
      </Button>
    </>
  )

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isNew ? 'Create Tag' : 'Edit Tag'}
      size="sm"
      footer={footer}
    >
      <div className="tag-edit-form">
        {error && <div className="error-banner">{error}</div>}

        <div className="form-group">
          <label htmlFor="tag-name">Name</label>
          <input
            id="tag-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Tag name..."
            autoFocus
          />
        </div>

        {!isNew && (
          <div className="form-group toggle-group">
            <label>
              <input
                type="checkbox"
                className="toggle"
                checked={archived}
                onChange={(e) => setArchived(e.target.checked)}
              />
              <span>Archived</span>
            </label>
            <p className="help-text">Archived tags won't appear in selection lists</p>
          </div>
        )}

        {!isNew && tag && (
          <div className="tag-stats-info">
            <div className="stat-item">
              <Icon name="ink_highlighter" className="icon" />
              <span>{tag.highlight_count || 0} highlights</span>
            </div>
            <div className="stat-item">
              <Icon name="menu_book" className="icon" />
              <span>{tag.article_count || 0} articles</span>
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}
