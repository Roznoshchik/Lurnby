import { useState, useRef } from 'preact/hooks'
import Badge from '../Badge/Badge'
import Button from '../Button/Button'
import Card from '../Card/Card'
import Combobox from '../Combobox/Combobox'
import Icon from '../Icon/Icon'
import Modal from '../Modal/Modal'
import QuillEditor from '../QuillEditor/QuillEditor'
import { api } from '../../services/api'
import { ROUTES } from '../../services/routes'
import './ArticleAddModal.css'

const webDescription = (
  <>
    <p>Parse the content from a provided url</p>
    <p>
      Paywalled sites cannot be parsed. Consider using <strong>Manual Entry</strong> and copying and
      pasting text directly.
    </p>
  </>
)

const pdfDescription = (
  <>
    <p>PDF support is experimental. </p>
    <p>
      Currently only text based PDFS can be processed, and PDFs with graphs, tables, or images are
      not processed well.
    </p>
  </>
)

const ARTICLE_TYPES = [
  {
    id: 'web',
    title: 'Web Article',
    description: webDescription,
    icon: 'link',
  },
  {
    id: 'epub',
    title: 'eBook',
    description: 'Upload an eBook with a .epub file extension',
    icon: 'menu_book',
  },
  {
    id: 'manual',
    title: 'Manual Entry',
    description: 'Write or paste content directly.',
    icon: 'edit_note',
  },
  {
    id: 'pdf',
    title: 'PDF',
    description: pdfDescription,
    icon: 'picture_as_pdf',
    badge: 'BETA',
  },
]

export default function ArticleAddModal({ isOpen, onClose, onSuccess, tags = [] }) {
  const [selectedType, setSelectedType] = useState(null)
  const [error, setError] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Form state
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState('')
  const [source, setSource] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [selectedTagIds, setSelectedTagIds] = useState([])

  // Content editor ref and state for re-render trigger
  const contentRef = useRef(null)
  const [hasContentState, setHasContentState] = useState(false)

  // Notes editor ref (optional for all types)
  const notesRef = useRef(null)

  const resetForm = () => {
    setSelectedType(null)
    setError(null)
    setUrl('')
    setTitle('')
    setSource('')
    setSelectedFile(null)
    setSelectedTagIds([])
    setIsSubmitting(false)
    setHasContentState(false)
    if (contentRef.current) {
      contentRef.current.setText('')
    }
    if (notesRef.current) {
      notesRef.current.setText('')
    }
  }

  const handleContentChange = () => {
    if (contentRef.current) {
      const text = contentRef.current.getText().trim()
      setHasContentState(text.length > 0)
    }
  }

  const handleClose = () => {
    resetForm()
    onClose()
  }

  const handleTypeSelect = (type) => {
    setSelectedType(type)
    setError(null)
  }

  const handleBack = () => {
    setSelectedType(null)
    setError(null)
  }

  const handleTagSelect = (tagId) => {
    setSelectedTagIds((prev) =>
      prev.includes(tagId) ? prev.filter((id) => id !== tagId) : [...prev, tagId],
    )
  }

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setError(null)
    }
  }

  const getContent = () => {
    if (!contentRef.current) return ''
    return contentRef.current.root.innerHTML
  }

  const getNotes = () => {
    if (!notesRef.current) return ''
    const text = notesRef.current.getText().trim()
    if (!text) return ''
    return notesRef.current.root.innerHTML
  }

  const hasContent = () => hasContentState

  const isFormValid = () => {
    if (!selectedType) return false

    switch (selectedType.id) {
      case 'web':
        return url.trim().length > 0
      case 'manual':
        return title.trim().length > 0 && hasContent()
      case 'epub':
      case 'pdf':
        return selectedFile !== null
      default:
        return false
    }
  }

  const handleSubmit = async () => {
    if (!isFormValid()) return

    setIsSubmitting(true)
    setError(null)

    try {
      const notes = getNotes()
      const data = { tag_ids: selectedTagIds }
      if (notes) {
        data.notes = notes
      }

      switch (selectedType.id) {
        case 'web':
          data.url = url.trim()
          break
        case 'manual':
          data.manual_entry = {
            title: title.trim(),
            content: getContent(),
            source: source.trim() || null,
          }
          break
        case 'epub':
          data.upload_file_ext = '.epub'
          data.filename = selectedFile?.name
          break
        case 'pdf':
          data.upload_file_ext = '.pdf'
          data.filename = selectedFile?.name
          break
      }

      const { data: response } = await api.post(ROUTES.API.ARTICLES, data)

      // For file uploads, we get a presigned URL
      if (response.upload_url && selectedFile) {
        try {
          const uploadResponse = await fetch(response.upload_url, {
            method: 'PUT',
            body: selectedFile,
          })
          if (!uploadResponse.ok) {
            throw new Error(`Upload failed: ${uploadResponse.status}`)
          }

          // Notify server that upload is complete - this starts the background task
          const { data: taskData } = await api.get(response.location, {
            upload_file_ext: response.upload_file_ext,
          })

          resetForm()
          onSuccess?.(taskData)
          return
        } catch (uploadErr) {
          // Clean up orphaned article if upload fails
          try {
            await api.delete(`/api/articles/${response.article.id}`)
          } catch {
            // Ignore cleanup errors
          }
          throw uploadErr
        }
      }

      resetForm()
      onSuccess?.({ article: response.article, processing: false })
    } catch (err) {
      let message = 'Failed to add article. Please try again.'
      if (err.status === 400) {
        message = 'Invalid request. Please check your input and try again.'
      } else if (err.status === 413) {
        message = 'File is too large. Please try a smaller file.'
      }
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const tagOptions = tags.map((tag) => ({
    value: tag.id,
    label: tag.name,
  }))

  const footer = selectedType ? (
    <>
      <Button variant="ghost" onClick={handleBack} disabled={isSubmitting}>
        Back
      </Button>
      <Button variant="default" onClick={handleSubmit} disabled={!isFormValid() || isSubmitting}>
        {isSubmitting ? 'Adding...' : 'Add Article'}
      </Button>
    </>
  ) : null

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Add a new article"
      size="lg"
      footer={footer}
      overlayClassName="article-add-modal"
    >
      <div className="article-add-form">
        {error && <div className="error-banner">{error}</div>}

        {/* Article Type Selection */}
        {!selectedType && (
          <div className="form-group">
            <span className="form-label">Choose article type:</span>
            <div className="article-type-cards">
              {ARTICLE_TYPES.map((type) => (
                <Card
                  key={type.id}
                  as="button"
                  interactive
                  padding="xl"
                  className="type-card"
                  onClick={() => handleTypeSelect(type)}
                >
                  {type.badge && (
                    <Badge variant="outline" className="type-card-badge">
                      <Icon name="construction" />
                      {type.badge}
                    </Badge>
                  )}
                  <div className="type-card-header">
                    <Icon name={type.icon} className="type-card-icon" />
                    <span className="type-card-title">{type.title}</span>
                  </div>
                  <div className="type-card-description">{type.description}</div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Selected Article Type + Tags Row */}
        {selectedType && (
          <div className="type-tags-row">
            <div className="form-group">
              <span className="form-label">Article type:</span>
              <div className="selected-type">
                <Badge variant="outline" className="type-badge">
                  <Icon name={selectedType.icon} />
                  {selectedType.title}
                </Badge>
                <Button variant="ghost" size="sm" onClick={handleBack} disabled={isSubmitting}>
                  Change
                </Button>
              </div>
            </div>
            <div className="form-group">
              <span className="form-label">Tags</span>
              <Combobox
                options={tagOptions}
                selected={selectedTagIds}
                onSelect={handleTagSelect}
                placeholder="Select tags..."
              />
            </div>
          </div>
        )}

        {/* Web Article Form */}
        {selectedType?.id === 'web' && (
          <div className="form-group">
            <label htmlFor="url" className="required">
              URL
            </label>
            <input
              type="url"
              id="url"
              value={url}
              onInput={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/article"
              disabled={isSubmitting}
            />
            <span className="help-text">Enter the full URL of the article you want to save</span>
          </div>
        )}

        {/* Manual Entry Form */}
        {selectedType?.id === 'manual' && (
          <>
            <div className="form-group">
              <label htmlFor="title" className="required">
                Title
              </label>
              <input
                type="text"
                id="title"
                value={title}
                onInput={(e) => setTitle(e.target.value)}
                placeholder="Article title"
                disabled={isSubmitting}
              />
            </div>
            <div className="form-group">
              <label htmlFor="source">Source</label>
              <input
                type="text"
                id="source"
                value={source}
                onInput={(e) => setSource(e.target.value)}
                placeholder="Optional: book name, author, website, etc."
                disabled={isSubmitting}
              />
            </div>
            <div className="form-group">
              <span className="form-label required">Content</span>
              <QuillEditor
                ref={contentRef}
                placeholder="Paste or write your content here..."
                readOnly={isSubmitting}
                onTextChange={handleContentChange}
              />
            </div>
          </>
        )}

        {/* File Upload Form (EPUB/PDF) */}
        {(selectedType?.id === 'epub' || selectedType?.id === 'pdf') && (
          <div className="form-group">
            <label htmlFor="file" className="required">
              {selectedType.id === 'epub' ? 'EPUB File' : 'PDF File'}
            </label>
            <div className="file-upload-area">
              <input
                type="file"
                id="file"
                accept={selectedType.id === 'epub' ? '.epub' : '.pdf'}
                onChange={handleFileChange}
                disabled={isSubmitting}
              />
              {selectedFile && (
                <div className="selected-file">
                  <Icon name="description" />
                  <span>{selectedFile.name}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedFile(null)}
                    disabled={isSubmitting}
                  >
                    <Icon name="close" />
                  </Button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Notes (optional, all article types) */}
        {selectedType && (
          <div className="form-group">
            <span className="form-label">Notes</span>
            <QuillEditor
              ref={notesRef}
              placeholder="Add personal notes about this article..."
              readOnly={isSubmitting}
            />
          </div>
        )}
      </div>
    </Modal>
  )
}
