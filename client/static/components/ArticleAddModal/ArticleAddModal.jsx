import { useState } from 'preact/hooks'
import Badge from '../Badge/Badge'
import Button from '../Button/Button'
import Card from '../Card/Card'
import Icon from '../Icon/Icon'
import Modal from '../Modal/Modal'
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

export default function ArticleAddModal({ isOpen, onClose }) {
  const [selectedType, setSelectedType] = useState(null)
  const [error, setError] = useState(null)

  const handleClose = () => {
    setSelectedType(null)
    setError(null)
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

  const footer = selectedType ? (
    <>
      <Button variant="ghost" onClick={handleBack}>
        Back
      </Button>
      <Button variant="default" disabled>
        Add Article
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
                  <p className="type-card-description">{type.description}</p>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Selected Article Type Display */}
        {selectedType && (
          <div className="form-group">
            <span className="form-label">Article type:</span>
            <div className="selected-type">
              <Badge variant="outline" className="type-badge">
                <Icon name={selectedType.icon} />
                {selectedType.title}
              </Badge>
              <Button variant="ghost" size="sm" onClick={handleBack}>
                Change
              </Button>
            </div>
          </div>
        )}

        {/* Type-specific forms will go here */}
        {selectedType && (
          <div className="type-form-placeholder">
            <Icon name="construction" />
            <p>Form for {selectedType.title} coming soon...</p>
          </div>
        )}
      </div>
    </Modal>
  )
}
