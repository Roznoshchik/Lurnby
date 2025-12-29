import Badge from '../Badge/Badge'
import Icon from '../Icon/Icon'
import Progress from '../Progress/Progress'
import './ArticleCard.css'

export default function ArticleCard({ article, onClick }) {
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

  const handleKeyDown = (e) => {
    // Space key and Enter key for accessibility
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onClick()
    }
  }

  return (
    <article onClick={onClick} onKeyDown={handleKeyDown} tabIndex={0} className="article-card">
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

        {/* Footer: Metadata */}
        <div className="article-footer">
          <div className="article-metadata">
            {article.read_time && (
              <div className="metadata-item">
                <Icon name="schedule" className="icon" />
                <span>{article.read_time} min</span>
              </div>
            )}
            {article.highlights_count > 0 && (
              <div className="metadata-item">
                <Icon name="ink_highlighter" className="icon" />
                <span>{article.highlights_count}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </article>
  )
}
