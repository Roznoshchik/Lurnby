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
import alert from './services/alertService'

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
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState('30')

  // Filter state (local, applied on button click)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('unarchived')

  // Applied filters (sent to server)
  const [appliedFilters, setAppliedFilters] = useState({
    q: '',
    status: 'unarchived',
  })

  // Modal states
  const [editingTag, setEditingTag] = useState(null)

  useEffect(() => {
    fetchTags()
  }, [page, perPage, appliedFilters])

  const fetchTags = async () => {
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

      const { data } = await api.get(ROUTES.API.TAGS, params)
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
    setPage(1)
    setAppliedFilters({
      q: searchQuery,
      status: statusFilter,
    })
  }

  const handlePerPageChange = (value) => {
    setPerPage(value)
    setPage(1)
  }

  const handleTagEdit = (tag) => {
    setEditingTag(tag)
  }

  const handleTagDelete = async (tag) => {
    if (!confirm(`Are you sure you want to delete "${tag.name}"? This cannot be undone.`)) {
      return
    }

    try {
      await api.delete(`${ROUTES.API.TAGS}/${tag.uuid}`)
      alert.success('Tag deleted')
      setTags((prev) => prev.filter((t) => t.id !== tag.id))
    } catch (err) {
      console.error('Error deleting tag:', err)
      alert.error('Failed to delete tag')
    }
  }

  const handleTagSaved = (savedTag) => {
    if (editingTag) {
      // Update existing tag
      const statusMatch =
        appliedFilters.status === 'all' ||
        (appliedFilters.status === 'archived' && savedTag.archived) ||
        (appliedFilters.status === 'unarchived' && !savedTag.archived)

      if (statusMatch) {
        setTags((prev) => prev.map((t) => (t.id === savedTag.id ? savedTag : t)))
      } else {
        // Tag no longer matches filter, remove from list
        setTags((prev) => prev.filter((t) => t.id !== savedTag.id))
      }
    } else {
      // New tag created - add to list if it matches current filter
      if (appliedFilters.status === 'unarchived' || appliedFilters.status === 'all') {
        setTags((prev) => [savedTag, ...prev])
      }
    }
  }

  const handleTagDeleted = (deletedTag) => {
    setTags((prev) => prev.filter((t) => t.id !== deletedTag.id))
  }

  const headerActions = (
    <Button variant="default" onClick={() => setShowCreateModal(true)}>
      <Icon name="add" />
      New Tag
    </Button>
  )

  return (
    <>
      <PageHeader
        title="Tags"
        icon="sell"
        subtitle="Organize your content"
        actions={headerActions}
      />

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
                Showing {(page - 1) * parseInt(perPage, 10) + 1}-
                {Math.min(page * parseInt(perPage, 10), total)} of {total} tags
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
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <Icon name="chevron_left" />
                </Button>
                <span className="pagination-info">Page {page}</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!hasNext}
                >
                  <Icon name="chevron_right" />
                </Button>
                <Select options={PER_PAGE_OPTIONS} value={perPage} onChange={handlePerPageChange} />
              </div>
            </>
          ) : (
            <div className="empty-state">
              <Icon name="sell" />
              <h3>No tags found</h3>
              <p>
                {appliedFilters.q
                  ? 'Try a different search term'
                  : 'Create your first tag to get started'}
              </p>
              {!appliedFilters.q && (
                <Button variant="default" onClick={() => setShowCreateModal(true)}>
                  <Icon name="add" />
                  Create Tag
                </Button>
              )}
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
