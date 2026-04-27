import Badge from '../Badge/Badge'
import Button from '../Button/Button'
import Card from '../Card/Card'
import Icon from '../Icon/Icon'
import Progress from '../Progress/Progress'
import './ArticleCard.css'

export default function ArticleCard({ article, openHref, onEdit, onViewHighlights }) {
  const getStatusIcon = () => {
    if (article.done) {
      return <Icon name="check_circle" className="icon status-done" />
    } else if (article.archived) {
      return <Icon name="archive" className="icon status-archived" />
    } else if (article.unread) {
      return <Icon name="circle" className="icon status-unread" />
    } else {
      return <Icon name="circle" filled className="icon status-in-progress" />
    }
  }

  return (
    <Card as="article" className="article-card" padding="lg">
      <div className="article-card-content">
        {/* Header: Source and Status */}
        <div className="article-card-header">
          <div className="article-source">
            <p>{article.source || 'Unknown Source'}</p>
          </div>
          <div className="article-status">{getStatusIcon()}</div>
        </div>

        {/* Title */}
        <h3 className="article-title">{article.title}</h3>

        {/* Progress Bar */}
        <div className="article-progress">
          <Progress value={article.progress || 0} className="progress-bar" />
          <p>{Math.round(article.progress || 0)}% complete</p>
        </div>

        {/* Tags */}
        {article.tags && article.tags.length > 0 && (
          <div className="article-tags">
            {article.tags.map((tag) => (
              <Badge key={tag.id} variant="outline" value={tag.name}>
                <Icon name="sell" className="icon" />
                {tag.name}
              </Badge>
            ))}
          </div>
        )}

        {/* Footer: Metadata and Actions */}
        <div className="article-footer">
          <div className="article-metadata">
            {article.read_time && (
              <div className="metadata-item">
                <Icon name="schedule" className="icon" />
                <span>{article.read_time} min</span>
              </div>
            )}
          </div>
          <div className="article-card-actions">
            <Button
              variant="ghost"
              size="sm"
              onClick={onEdit}
              className="icon-button"
              aria-label="Edit article"
            >
              <Icon name="edit_square" />
            </Button>
            {article.highlights_count > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onViewHighlights}
                className="icon-button"
                aria-label="View highlights"
              >
                <Icon name="ink_highlighter" />
              </Button>
            )}
            <a
              href={openHref}
              className="btn btn-ghost btn-sm icon-button"
              aria-label="Read article"
            >
              <Icon name="visibility" />
            </a>
          </div>
        </div>
      </div>
    </Card>
  )
}
