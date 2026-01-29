import { render } from 'preact'
import { useEffect, useState, useMemo } from 'preact/hooks'
import alert from './services/alertService'
import './css/globals.css'
import './css/articles.css'
import ArticleAddModal from './components/ArticleAddModal/ArticleAddModal'
import ArticleCard from './components/ArticleCard/ArticleCard'
import ArticleEditModal from './components/ArticleEditModal/ArticleEditModal'
import ArticlePreview from './components/ArticlePreview/ArticlePreview'
import Badge from './components/Badge/Badge'
import Button from './components/Button/Button'
import Combobox from './components/Combobox/Combobox'
import Icon from './components/Icon/Icon'
import PageHeader from './components/PageHeader/PageHeader'
import Select from './components/Select/Select'
import { Layout } from './components/Layout/Layout'
import RequireAuth from './components/RequireAuth/RequireAuth'
import { AuthProvider } from './contexts/AuthContext/AuthContext'
import pollService from './services/pollService'
import { api } from './services/api'
import { ROUTES } from './services/routes'
import { getReadableSource } from './utils/sourceFormatter'
import { useUrlParams } from './hooks/useUrlParams'

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

  // URL-synced pagination and filters
  const [params, setParams] = useUrlParams({
    page: 1,
    perPage: '15',
    q: '',
    status: '',
    tag_ids: '',
  })

  // Local filter state (for form inputs, applied on button click)
  const [searchQuery, setSearchQuery] = useState(params.q)
  const [statusFilter, setStatusFilter] = useState(params.status)
  const [selectedTags, setSelectedTags] = useState(
    params.tag_ids ? params.tag_ids.split(',').map(Number) : [],
  )

  // Modal states
  const [editingArticle, setEditingArticle] = useState(null)
  const [showAddModal, setShowAddModal] = useState(false)

  useEffect(() => {
    fetchTags()
  }, [])

  useEffect(() => {
    fetchArticles()
  }, [params.page, params.perPage, params.q, params.status, params.tag_ids])

  const fetchArticles = async () => {
    try {
      setLoading(true)
      const queryParams = {
        page: params.page,
        per_page: params.perPage,
        q: params.q,
        status: params.status,
        tag_ids: params.tag_ids,
      }
      // Remove empty params
      Object.keys(queryParams).forEach((key) => {
        if (!queryParams[key]) delete queryParams[key]
      })

      const { data } = await api.get('/api/articles', queryParams)
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
      const { data } = await api.get('/api/tags', { per_page: 'all' })
      setAllTags(data.tags || [])
    } catch (err) {
      console.error('Error fetching tags:', err)
    }
  }

  const applyFilters = () => {
    setParams({
      page: 1,
      q: searchQuery,
      status: statusFilter,
      tag_ids: selectedTags.join(','),
    })
  }

  const toggleTag = (tagId) => {
    setSelectedTags((prev) =>
      prev.includes(tagId) ? prev.filter((id) => id !== tagId) : [...prev, tagId],
    )
  }

  const handlePerPageChange = (value) => {
    setParams({ perPage: value, page: 1 })
  }

  const tagOptions = useMemo(
    () =>
      allTags.map((tag) => ({
        value: tag.id,
        label: tag.name,
      })),
    [allTags],
  )

  const selectedTagObjects = useMemo(
    () => allTags.filter((tag) => selectedTags.includes(tag.id)),
    [allTags, selectedTags],
  )

  const handleArticleOpen = (article) => {
    window.location.href = ROUTES.PAGES.reader(article.uuid)
  }

  const handleArticleEdit = (article) => {
    setEditingArticle(article)
  }

  const handleViewHighlights = (article) => {
    window.location.href = ROUTES.PAGES.articleHighlights(article.uuid)
  }

  const handleArticleSaved = (updatedArticle) => {
    const isViewingArchived = params.status === 'archived'
    const articleIsArchived = updatedArticle.archived

    // If archive status doesn't match current filter, remove from list
    if (isViewingArchived !== articleIsArchived) {
      setArticles((prev) => prev.filter((a) => a.id !== updatedArticle.id))
      setRecentArticles((prev) => prev.filter((a) => a.id !== updatedArticle.id))
    } else {
      // Update the article in both lists
      setArticles((prev) => prev.map((a) => (a.id === updatedArticle.id ? updatedArticle : a)))
      setRecentArticles((prev) =>
        prev.map((a) => (a.id === updatedArticle.id ? updatedArticle : a)),
      )
    }
  }

  return (
    <>
      <PageHeader
        title="Articles"
        icon="menu_book"
        subtitle="Your Reading Library"
        action={
          <Button variant="default" icon="add" onClick={() => setShowAddModal(true)}>
            Add Article
          </Button>
        }
      />

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
                  <Select
                    options={STATUS_OPTIONS}
                    value={statusFilter}
                    onChange={setStatusFilter}
                  />
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
                  Showing {(params.page - 1) * parseInt(params.perPage, 10) + 1}-
                  {Math.min(params.page * parseInt(params.perPage, 10), total)} of {total} articles
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
                      onViewHighlights={() => handleViewHighlights(article)}
                    />
                  ))}
                </div>

                {/* Pagination */}
                <div className="pagination">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setParams({ page: Math.max(1, params.page - 1) })}
                    disabled={params.page === 1}
                  >
                    <Icon name="chevron_left" />
                  </Button>
                  <span className="pagination-info">Page {params.page}</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setParams({ page: params.page + 1 })}
                    disabled={!hasNext}
                  >
                    <Icon name="chevron_right" />
                  </Button>
                  <Select
                    options={PER_PAGE_OPTIONS}
                    value={params.perPage}
                    onChange={handlePerPageChange}
                  />
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

      {/* Edit Article Modal */}
      {editingArticle && (
        <ArticleEditModal
          article={editingArticle}
          allTags={allTags}
          isOpen={!!editingArticle}
          onClose={() => setEditingArticle(null)}
          onSave={handleArticleSaved}
          onTagCreate={(tag) => setAllTags((prev) => [...prev, tag])}
        />
      )}

      {/* Add Article Modal */}
      <ArticleAddModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        tags={allTags}
        onTagCreate={(tag) => setAllTags((prev) => [...prev, tag])}
        onSuccess={(response) => {
          setShowAddModal(false)
          const { article, processing, task_id } = response
          const articleTitle = article?.title || 'File'

          if (!processing) {
            alert.success(`"${articleTitle}" added`)
            fetchArticles()
            return
          }

          alert.info(`Processing "${articleTitle}"...`, {
            description: 'This may take a moment',
          })

          pollService.poll({
            taskName: task_id,
            endpoint: ROUTES.API.task(task_id),
            onDone: () => {
              alert.success(`"${articleTitle}" is ready`)
              fetchArticles()
            },
            onCancel: (reason) => {
              alert.error('Processing failed', {
                description: reason,
              })
            },
            shouldCancel: [
              pollService.stopAfterAttempts(60),
              pollService.stopAfterTime(5 * 60 * 1000),
            ],
            frequency: 3000,
          })
        }}
      />
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
