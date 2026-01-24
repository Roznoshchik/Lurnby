import { useEffect, useState } from 'preact/hooks'
import Icon from '../Icon/Icon'
import { api } from '../../services/api'
import { ROUTES } from '../../services/routes'
import './PageHeader.css'

export default function PageHeader({ title, icon, subtitle, action }) {
  const [monthlyStats, setMonthlyStats] = useState({
    reviewEvents: 0,
    articlesOpened: 0,
    highlightsAdded: 0,
  })

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const { data } = await api.get(ROUTES.API.STATS)
      setMonthlyStats({
        reviewEvents: data.reviews_this_month,
        articlesOpened: data.articles_opened_this_month,
        highlightsAdded: data.highlights_added_this_month,
      })
    } catch (err) {
      console.error('Error fetching stats:', err)
    }
  }

  return (
    <header className="page-header">
      <div className="page-header-content">
        <div className="page-header-top">
          <div className="page-header-title">
            <Icon name={icon} />
            <h1>{title}</h1>
            <span className="page-header-subtitle">{subtitle}</span>
          </div>
          {action}
        </div>

        <div className="stats-grid">
          <div className="stat-card stat-reviews">
            <div className="stat-icon">
              <Icon name="exercise" />
            </div>
            <div className="stat-content">
              <div className="stat-value">{monthlyStats.reviewEvents}</div>
              <div className="stat-label">Review Events</div>
              <div className="stat-period">This Month</div>
            </div>
          </div>

          <div className="stat-card stat-articles">
            <div className="stat-icon">
              <Icon name="book" />
            </div>
            <div className="stat-content">
              <div className="stat-value">{monthlyStats.articlesOpened}</div>
              <div className="stat-label">Articles Opened</div>
              <div className="stat-period">This Month</div>
            </div>
          </div>

          <div className="stat-card stat-highlights">
            <div className="stat-icon">
              <Icon name="ink_highlighter" />
            </div>
            <div className="stat-content">
              <div className="stat-value">{monthlyStats.highlightsAdded}</div>
              <div className="stat-label">Highlights Added</div>
              <div className="stat-period">This Month</div>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
