import { render } from 'preact'
import { useEffect, useState } from 'preact/hooks'
import './css/globals.css'
import './css/tags.css'
import Button from './components/Button/Button'
import Icon from './components/Icon/Icon'
import PageHeader from './components/PageHeader/PageHeader'
import Select from './components/Select/Select'
import TagCard from './components/TagCard/TagCard'
import TagEditModal from './components/TagEditModal/TagEditModal'
import { Layout } from './components/Layout/Layout'
import RequireAuth from './components/RequireAuth/RequireAuth'
import { AuthProvider } from './contexts/AuthContext/AuthContext'
import { api } from './services/api'
import { ROUTES } from './services/routes'
import { useUrlParams } from './hooks/useUrlParams'

const STATUS_OPTIONS = [
  { value: 'unarchived', label: 'Active' },
  { value: 'archived', label: 'Archived' },
  { value: 'all', label: 'All' },
]

const PER_PAGE_OPTIONS = [
  { value: '30', label: '30 per page' },
  { value: '50', label: '50 per page' },
  { value: '100', label: '100 per page' },
]

function TagsList() {
  const [tags, setTags] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hasNext, setHasNext] = useState(false)
  const [total, setTotal] = useState(0)

  // URL-synced pagination and filters
  const [params, setParams] = useUrlParams({
    page: 1,
    perPage: '30',
    q: '',
    status: 'unarchived',
  })

  // Local filter state (for form inputs, applied on button click)
  const [searchQuery, setSearchQuery] = useState(params.q)
  const [statusFilter, setStatusFilter] = useState(params.status)

  // Modal states
  const [editingTag, setEditingTag] = useState(null)

  useEffect(() => {
    fetchTags()
  }, [params.page, params.perPage, params.q, params.status])

  const fetchTags = async () => {
    try {
      setLoading(true)
      const queryParams = {
        page: params.page,
        per_page: params.perPage,
        q: params.q,
        status: params.status,
      }
      // Remove empty params
      Object.keys(queryParams).forEach((key) => {
        if (!queryParams[key]) delete queryParams[key]
      })

      const { data } = await api.get(ROUTES.API.TAGS, queryParams)
      setTags(data.tags || [])
      setHasNext(data.has_next || false)
      setTotal(data.total || 0)
      setError(null)
    } catch (err) {
      console.error('Error fetching tags:', err)
      setError('Failed to load tags')
    } finally {
      setLoading(false)
    }
  }

  const applyFilters = () => {
    setParams({
      page: 1,
      q: searchQuery,
      status: statusFilter,
    })
  }

  const handlePerPageChange = (value) => {
    setParams({ perPage: value, page: 1 })
  }

  const handleTagEdit = (tag) => {
    setEditingTag(tag)
  }

  const handleTagSaved = (savedTag) => {
    if (editingTag) {
      // Update existing tag
      const statusMatch =
        params.status === 'all' ||
        (params.status === 'archived' && savedTag.archived) ||
        (params.status === 'unarchived' && !savedTag.archived)

      if (statusMatch) {
        setTags((prev) => prev.map((t) => (t.id === savedTag.id ? savedTag : t)))
      } else {
        // Tag no longer matches filter, remove from list
        setTags((prev) => prev.filter((t) => t.id !== savedTag.id))
      }
    } else {
      // New tag created - add to list if it matches current filter
      if (params.status === 'unarchived' || params.status === 'all') {
        setTags((prev) => [savedTag, ...prev])
      }
    }
  }

  const handleTagDeleted = (deletedTag) => {
    setTags((prev) => prev.filter((t) => t.id !== deletedTag.id))
  }

  return (
    <>
      <PageHeader title="Tags" icon="sell" subtitle="Organize your content" />

      {loading && (
        <div className="content-container">
          <div className="loading-state">
            <p>Loading tags...</p>
          </div>
        </div>
      )}

      {error && (
        <div className="content-container">
          <div className="error-state">
            <p>{error}</p>
            <Button onClick={fetchTags}>Retry</Button>
          </div>
        </div>
      )}

      {!loading && !error && (
        <div className="content-container">
          {/* Filters */}
          <div className="filters-section">
            <div className="filter-row">
              <Icon name="search" className="filter-icon" />
              <input
                type="text"
                placeholder="Search tags..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
            </div>

            <div className="filter-row filter-controls">
              <div className="filter-group">
                <Icon name="filter_alt" className="filter-icon" />
                <span className="filter-label">Status:</span>
                <Select options={STATUS_OPTIONS} value={statusFilter} onChange={setStatusFilter} />
              </div>

              <Button variant="default" size="sm" onClick={applyFilters}>
                <Icon name="check" />
                Apply
              </Button>
            </div>

            {total > 0 && (
              <div className="tags-count">
                Showing {(params.page - 1) * parseInt(params.perPage, 10) + 1}-
                {Math.min(params.page * parseInt(params.perPage, 10), total)} of {total} tags
              </div>
            )}
          </div>

          {/* Tags Grid */}
          {tags.length > 0 ? (
            <>
              <div className="tags-grid">
                {tags.map((tag) => (
                  <TagCard key={tag.id} tag={tag} onEdit={() => handleTagEdit(tag)} />
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
                <Select options={PER_PAGE_OPTIONS} value={params.perPage} onChange={handlePerPageChange} />
              </div>
            </>
          ) : (
            <div className="empty-state">
              <Icon name="sell" />
              <h3>No tags found</h3>
              <p>
                {params.q
                  ? 'Try a different search term'
                  : 'Create tags when adding highlights or articles'}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Edit Tag Modal */}
      {editingTag && (
        <TagEditModal
          tag={editingTag}
          isOpen={!!editingTag}
          onClose={() => setEditingTag(null)}
          onSave={handleTagSaved}
          onDelete={handleTagDeleted}
        />
      )}
    </>
  )
}

function TagsPage() {
  return (
    <AuthProvider>
      <RequireAuth>
        <Layout>
          <TagsList />
        </Layout>
      </RequireAuth>
    </AuthProvider>
  )
}

render(<TagsPage />, document.getElementById('app'))
