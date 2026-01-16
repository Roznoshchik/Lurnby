import Badge from '../Badge/Badge'
import Card from '../Card/Card'
import Icon from '../Icon/Icon'
import { getTagColorClass } from '../../utils/helpers'
import './TagCard.css'

export default function TagCard({ tag, onEdit }) {
  const colorClass = getTagColorClass(tag.name)

  return (
    <Card as="article" className="tag-card" padding="md" interactive onClick={onEdit}>
      <div className="tag-card-content">
        <div className="tag-card-header">
          <span className={`tag-color-indicator ${colorClass}`} />
          <h3 className="tag-name">{tag.name}</h3>
          {tag.archived && (
            <Badge variant="secondary" className="archived-badge">
              Archived
            </Badge>
          )}
        </div>

        <div className="tag-stats">
          <div className="tag-stat">
            <Icon name="ink_highlighter" className="icon" />
            <span>{tag.highlight_count || 0} highlights</span>
          </div>
          <div className="tag-stat">
            <Icon name="menu_book" className="icon" />
            <span>{tag.article_count || 0} articles</span>
          </div>
        </div>
      </div>
    </Card>
  )
}
