import Button from '../Button/Button'
import Icon from '../Icon/Icon'
import Progress from '../Progress/Progress'
import './ArticlePreview.css'

export default function ArticlePreview({ article, onOpen, onEdit }) {
  const getStatusIcon = () => {
    if (article.done) {
      return <Icon name="check_circle" className="status-icon status-done" />
    } else if (article.archived) {
      return <Icon name="archive" className="status-icon status-archived" />
    } else if (article.unread) {
      return <Icon name="circle" className="status-icon status-unread" />
    } else {
      return <Icon name="circle" filled className="status-icon status-in-progress" />
    }
  }

  const progress = Math.round(article.progress ?? 0)

  return (
    <div className="article-preview">
      <div className="article-preview-header">
        <h3 className="article-preview-title">{article.title}</h3>
        <div className="article-preview-status">{getStatusIcon()}</div>
      </div>

      <div className="article-preview-progress">
        <Progress value={progress} className="preview-progress-bar" />
        <span className="progress-text">{progress}% complete</span>
      </div>

      <div className="article-preview-footer">

        <div className="article-preview-actions">
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation()
              onEdit()
            }}
            className="icon-button"
            aria-label="Edit article"
          >
            <Icon name="edit" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation()
              onOpen()
            }}
            className="icon-button"
            aria-label="Open article"
          >
            <Icon name="open_in_new" />
          </Button>
        </div>
      </div>
    </div>
  )
}
