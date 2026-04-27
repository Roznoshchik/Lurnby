import Badge from '../Badge/Badge'
import Button from '../Button/Button'
import Card from '../Card/Card'
import Icon from '../Icon/Icon'
import './HighlightCard.css'

const hasContent = (html) => {
  if (!html) return false
  const text = html.replace(/<[^>]*>/g, '').trim()
  return text.length > 0
}

export default function HighlightCard({ highlight, onEdit, viewInArticleHref }) {
  return (
    <Card as="article" className="highlight-card" padding="lg">
      <div className="highlight-card-content">
        {/* Header: Source and Article Title */}
        <div className="highlight-card-header">
          <p className="highlight-source">{highlight.source || 'Unknown Source'}</p>
          {highlight.article_title && (
            <p className="highlight-article-title">{highlight.article_title}</p>
          )}
        </div>

        <div className="highlight-divider" />

        {/* Highlight Text (HTML content) */}
        <div
          className="highlight-text"
          dangerouslySetInnerHTML={{ __html: highlight.text || '' }}
        />

        {/* Note (if exists, also HTML) */}
        {hasContent(highlight.note) && (
          <div className="highlight-note">
            <Icon name="note" className="icon" />
            <div dangerouslySetInnerHTML={{ __html: highlight.note }} />
          </div>
        )}

        <div className="highlight-divider" />

        {/* Tags */}
        {highlight.tags && highlight.tags.length > 0 && (
          <div className="highlight-tags">
            {highlight.tags.map((tag) => (
              <Badge key={tag.id} variant="outline" value={tag.name}>
                <Icon name="sell" className="icon" />
                {tag.name}
              </Badge>
            ))}
          </div>
        )}

        {/* Footer: Metadata and Actions */}
        <div className="highlight-footer">
          <div className="highlight-metadata">
            <div className="metadata-item">
              <Icon name="schedule" className="icon" />
              <span>{new Date(highlight.created_date).toLocaleDateString()}</span>
            </div>
          </div>
          <div className="highlight-card-actions">
            <Button
              variant="ghost"
              size="sm"
              onClick={onEdit}
              className="icon-button"
              aria-label="Edit highlight"
            >
              <Icon name="edit_square" />
            </Button>
            {highlight.article_uuid && viewInArticleHref && (
              <a
                href={viewInArticleHref}
                className="btn btn-ghost btn-sm icon-button"
                aria-label="View in article"
              >
                <Icon name="visibility" />
              </a>
            )}
          </div>
        </div>
      </div>
    </Card>
  )
}
