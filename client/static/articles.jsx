import { render } from 'preact'
import { useEffect, useState, useMemo } from 'preact/hooks'
import './css/globals.css'
import './css/articles.css'
import ArticleCard from './components/ArticleCard/ArticleCard'
import ArticlePreview from './components/ArticlePreview/ArticlePreview'
import Badge from './components/Badge/Badge'
import Button from './components/Button/Button'
import Combobox from './components/Combobox/Combobox'
import Icon from './components/Icon/Icon'
import Select from './components/Select/Select'
import { Layout } from './components/Layout/Layout'
import RequireAuth from './components/RequireAuth/RequireAuth'
import { AuthProvider } from './contexts/AuthContext/AuthContext'
import { api } from './utils/api'
import { ROUTES } from './utils/routes'
import { getReadableSource } from './utils/sourceFormatter'

const STATUS_OPTIONS = [
  { value: '', label: 'All (non-archived)' },
  { value: 'unread', label: 'Unread' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'read', label: 'Read' },
  { value: 'archived', label: 'Archived' },
]

const PER_PAGE_OPTIONS = [
  { value: '15', label: '15 per page' },
  { value: '30', label: '30 per page' },
  { value: '50', label: '50 per page' },
]

function ArticlesList() {
  const [recentArticles, setRecentArticles] = useState([])
  const [articles, setArticles] = useState([])
  const [allTags, setAllTags] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hasNext, setHasNext] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState('15')
  const [monthlyStats, setMonthlyStats] = useState({
    reviewEvents: 0,
    articlesOpened: 0,
    highlightsAdded: 0,
  })

  // Filter state (local, applied on button click)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [selectedTags, setSelectedTags] = useState([])

  // Applied filters (sent to server)
  const [appliedFilters, setAppliedFilters] = useState({
    q: '',
    status: '',
    tag_ids: '',
  })

  useEffect(() => {
    fetchTags()
    fetchStats()
  }, [])

  useEffect(() => {
    fetchArticles()
  }, [page, perPage, appliedFilters])

  const fetchArticles = async () => {
    try {
      setLoading(true)
      const params = {
        page,
        per_page: perPage,
        ...appliedFilters,
      }
      // Remove empty params
      Object.keys(params).forEach((key) => {
        if (!params[key]) delete params[key]
      })

      const data = await api.get('/api/articles', params)
      setRecentArticles(data.recent || [])
      setArticles(data.articles || [])
      setHasNext(data.has_next || false)
      setTotal(data.total || 0)
      setError(null)
    } catch (err) {
      console.error('Error fetching articles:', err)
      setError('Failed to load articles')
    } finally {
      setLoading(false)
    }
  }

  const fetchTags = async () => {
    try {
      const data = await api.get('/api/tags', { per_page: 'all' })
      setAllTags(data.tags || [])
    } catch (err) {
      console.error('Error fetching tags:', err)
    }
  }

  const fetchStats = async () => {
    try {
      const data = await api.get(ROUTES.API.STATS)
      setMonthlyStats({
        reviewEvents: data.reviews_this_month,
        articlesOpened: data.articles_opened_this_month,
        highlightsAdded: data.highlights_added_this_month,
      })
    } catch (err) {
      console.error('Error fetching stats:', err)
    }
  }

  const applyFilters = () => {
    setPage(1)
    setAppliedFilters({
      q: searchQuery,
      status: statusFilter,
      tag_ids: selectedTags.join(','),
    })
  }

  const toggleTag = (tagId) => {
    setSelectedTags((prev) => (prev.includes(tagId) ? prev.filter((id) => id !== tagId) : [...prev, tagId]))
  }

  const handlePerPageChange = (value) => {
    setPerPage(value)
    setPage(1)
  }

  const tagOptions = useMemo(
    () =>
      allTags.map((tag) => ({
        value: tag.id,
        label: tag.name,
      })),
    [allTags]
  )

  const selectedTagObjects = useMemo(
    () => allTags.filter((tag) => selectedTags.includes(tag.id)),
    [allTags, selectedTags]
  )

  const handleArticleOpen = (article) => {
    // TODO: Navigate to article reader page
    console.log('Open article:', article)
  }

  const handleArticleEdit = (article) => {
    // TODO: Open edit modal
    console.log('Edit article:', article)
  }

  return (
    <>
      {/* Page Header */}
      <header className="page-header">
        <div className="page-header-content">
          <div className="page-header-top">
            <div className="page-header-title">
              <Icon name="menu_book" />
              <h1>Articles</h1>
              <span className="page-header-subtitle">Your Reading Library</span>
            </div>
            <Button variant="default" icon="add" onClick={() => console.log('Add new article')}>
              Add Article
            </Button>
          </div>

          {/* Monthly Stats */}
          <div className="stats-grid">
            <div className="stat-card stat-reviews">
              <div className="stat-icon">
                <Icon name="rotate_left" />
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

      {loading && (
        <div className="content-container">
          <div className="loading-state">
            <p>Loading articles...</p>
          </div>
        </div>
      )}

      {error && (
        <div className="content-container">
          <div className="error-state">
            <p>{error}</p>
            <Button onClick={fetchArticles}>Retry</Button>
          </div>
        </div>
      )}

      {!loading && !error && (
        <div className="content-container">
          {/* Section 1: Recently Opened */}
          {recentArticles.length > 0 && (
            <section className="recent-section">
              <h2 className="section-title">
                <Icon name="schedule" />
                Recently Opened
              </h2>
              <div className="recent-previews">
                {recentArticles.map((article) => (
                  <ArticlePreview
                    key={article.id}
                    article={{
                      ...article,
                      source: getReadableSource(article.source),
                    }}
                    onOpen={() => handleArticleOpen(article)}
                    onEdit={() => handleArticleEdit(article)}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Section 2: All Articles with Filters */}
          <section className="all-articles-section">
            <h2 className="section-title">
              <Icon name="library_books" />
              All Articles
            </h2>

            {/* Filters */}
            <div className="filters-section">
              {/* Search Bar */}
              <div className="filter-row">
                <Icon name="search" className="filter-icon" />
                <input
                  type="text"
                  placeholder="Search articles by title or source..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="search-input"
                />
              </div>

              {/* Status and Tags Filter */}
              <div className="filter-row filter-controls">
                <div className="filter-group">
                  <Icon name="filter_alt" className="filter-icon" />
                  <span className="filter-label">Status:</span>
                  <Select options={STATUS_OPTIONS} value={statusFilter} onChange={setStatusFilter} />
                </div>

                {allTags.length > 0 && (
                  <div className="filter-group">
                    <Icon name="sell" className="filter-icon" />
                    <span className="filter-label">Tags:</span>
                    <Combobox
                      options={tagOptions}
                      selected={selectedTags}
                      onSelect={toggleTag}
                      placeholder="Select tags..."
                    />
                  </div>
                )}

                <Button variant="default" size="sm" onClick={applyFilters}>
                  <Icon name="check" />
                  Apply
                </Button>
              </div>

              {/* Selected Tags Display */}
              {selectedTagObjects.length > 0 && (
                <div className="selected-tags">
                  {selectedTagObjects.map((tag) => (
                    <Badge
                      key={tag.id}
                      variant="outline"
                      value={tag.name}
                      className="tag-badge"
                      onClick={() => toggleTag(tag.id)}
                    >
                      {tag.name}
                      <Icon name="close" className="tag-remove" />
                    </Badge>
                  ))}
                </div>
              )}

              {/* Articles Count */}
              {total > 0 && (
                <div className="articles-count">
                  Showing {(page - 1) * parseInt(perPage) + 1}-
                  {Math.min(page * parseInt(perPage), total)} of {total} articles
                </div>
              )}
            </div>

            {/* Articles Grid */}
            {articles.length > 0 ? (
              <>
                <div className="articles-grid">
                  {articles.map((article) => (
                    <ArticleCard
                      key={article.id}
                      article={{
                        ...article,
                        source: getReadableSource(article.source),
                      }}
                      onOpen={() => handleArticleOpen(article)}
                      onEdit={() => handleArticleEdit(article)}
                    />
                  ))}
                </div>

                {/* Pagination */}
                <div className="pagination">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    <Icon name="chevron_left" />
                  </Button>
                  <span className="pagination-info">Page {page}</span>
                  <Button variant="outline" size="sm" onClick={() => setPage((p) => p + 1)} disabled={!hasNext}>
                    <Icon name="chevron_right" />
                  </Button>
                  <Select options={PER_PAGE_OPTIONS} value={perPage} onChange={handlePerPageChange} />
                </div>
              </>
            ) : (
              <div className="empty-state">
                <Icon name="description" />
                <h3>No articles found</h3>
                <p>Try adjusting your search or filters</p>
              </div>
            )}
          </section>
        </div>
      )}
    </>
  )
}

function ArticlesPage() {
  return (
    <AuthProvider>
      <RequireAuth>
        <Layout>
          <ArticlesList />
        </Layout>
      </RequireAuth>
    </AuthProvider>
  )
}

render(<ArticlesPage />, document.getElementById('app'))
