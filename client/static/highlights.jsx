import { render } from 'preact'
import { useEffect, useState, useMemo } from 'preact/hooks'
import './css/globals.css'
import './css/highlights.css'
import Badge from './components/Badge/Badge'
import Button from './components/Button/Button'
import Combobox from './components/Combobox/Combobox'
import HighlightCard from './components/HighlightCard/HighlightCard'
import HighlightEditModal from './components/HighlightEditModal/HighlightEditModal'
import Icon from './components/Icon/Icon'
import PageHeader from './components/PageHeader/PageHeader'
import Select from './components/Select/Select'
import { Layout } from './components/Layout/Layout'
import RequireAuth from './components/RequireAuth/RequireAuth'
import { AuthProvider } from './contexts/AuthContext/AuthContext'
import { api } from './services/api'
import { ROUTES } from './services/routes'
import { getReadableSource } from './utils/sourceFormatter'
import { useUrlParams } from './hooks/useUrlParams'

const TAG_STATUS_OPTIONS = [
  { value: '', label: 'All' },
  { value: 'tagged', label: 'With Tags' },
  { value: 'untagged', label: 'Without Tags' },
]

const PER_PAGE_OPTIONS = [
  { value: '15', label: '15 per page' },
  { value: '30', label: '30 per page' },
  { value: '50', label: '50 per page' },
]

function HighlightsList() {
  const [highlights, setHighlights] = useState([])
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
    tag_status: '',
    tag_ids: '',
    article: '',
  })

  // Local filter state (for form inputs, applied on button click)
  const [searchQuery, setSearchQuery] = useState(params.q)
  const [tagStatusFilter, setTagStatusFilter] = useState(params.tag_status)
  const [selectedTags, setSelectedTags] = useState(
    params.tag_ids ? params.tag_ids.split(',').map(Number) : [],
  )

  // Modal states
  const [editingHighlight, setEditingHighlight] = useState(null)

  useEffect(() => {
    fetchTags()
  }, [])

  useEffect(() => {
    fetchHighlights()
  }, [params.page, params.perPage, params.q, params.tag_status, params.tag_ids, params.article])

  const fetchHighlights = async () => {
    try {
      setLoading(true)
      const queryParams = {
        page: params.page,
        per_page: params.perPage,
        q: params.q,
        tag_status: params.tag_status,
        tag_ids: params.tag_ids,
        article_uuid: params.article,
      }
      // Remove empty params
      Object.keys(queryParams).forEach((key) => {
        if (!queryParams[key]) delete queryParams[key]
      })

      const { data } = await api.get(ROUTES.API.HIGHLIGHTS, queryParams)
      setHighlights(data.highlights || [])
      setHasNext(data.has_next || false)
      setTotal(data.total || 0)
      setError(null)
    } catch (err) {
      console.error('Error fetching highlights:', err)
      setError('Failed to load highlights')
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
      tag_status: tagStatusFilter,
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

  const handleHighlightEdit = (highlight) => {
    setEditingHighlight(highlight)
  }

  const handleViewInArticle = (highlight) => {
    if (!highlight.article_uuid) return

    if (highlight.start_chunk != null) {
      window.location.href = ROUTES.PAGES.reader(highlight.article_uuid, {
        chunk: highlight.start_chunk,
        offset: highlight.start ?? 0,
      })
    } else {
      window.location.href = ROUTES.PAGES.reader(highlight.article_uuid, {
        unprocessed: true,
        highlight: highlight.uuid,
      })
    }
  }

  const handleHighlightSaved = (updatedHighlight) => {
    setHighlights((prev) =>
      prev.map((h) => (h.id === updatedHighlight.id ? updatedHighlight : h)),
    )
  }

  return (
    <>
      <PageHeader title="Highlights" icon="ink_highlighter" subtitle="Your Knowledge Library" />

      {loading && (
        <div className="content-container">
          <div className="loading-state">
            <p>Loading highlights...</p>
          </div>
        </div>
      )}

      {error && (
        <div className="content-container">
          <div className="error-state">
            <p>{error}</p>
            <Button onClick={fetchHighlights}>Retry</Button>
          </div>
        </div>
      )}

      {!loading && !error && (
        <div className="content-container">
          {/* Filters */}
          <div className="filters-section">
            {/* Search Bar */}
            <div className="filter-row">
              <Icon name="search" className="filter-icon" />
              <input
                type="text"
                placeholder="Search highlights by text, note, or article..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
            </div>

            {/* Tag Status and Tags Filter */}
            <div className="filter-row filter-controls">
              <div className="filter-group">
                <Icon name="filter_alt" className="filter-icon" />
                <span className="filter-label">Filter:</span>
                <Select
                  options={TAG_STATUS_OPTIONS}
                  value={tagStatusFilter}
                  onChange={setTagStatusFilter}
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

            {/* Highlights Count */}
            {total > 0 && (
              <div className="highlights-count">
                Showing {(params.page - 1) * parseInt(params.perPage, 10) + 1}-
                {Math.min(params.page * parseInt(params.perPage, 10), total)} of {total} highlights
              </div>
            )}
          </div>

          {/* Highlights Grid */}
          {highlights.length > 0 ? (
            <>
              <div className="highlights-grid">
                {highlights.map((highlight) => (
                  <HighlightCard
                    key={highlight.id}
                    highlight={{
                      ...highlight,
                      source: getReadableSource(highlight.source),
                    }}
                    onEdit={() => handleHighlightEdit(highlight)}
                    onViewInArticle={() => handleViewInArticle(highlight)}
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
                <Select options={PER_PAGE_OPTIONS} value={params.perPage} onChange={handlePerPageChange} />
              </div>
            </>
          ) : (
            <div className="empty-state">
              <Icon name="ink_highlighter" />
              <h3>No highlights found</h3>
              <p>Try adjusting your search or filters</p>
            </div>
          )}
        </div>
      )}

      {/* Edit Highlight Modal */}
      {editingHighlight && (
        <HighlightEditModal
          highlight={editingHighlight}
          allTags={allTags}
          isOpen={!!editingHighlight}
          onClose={() => setEditingHighlight(null)}
          onSave={handleHighlightSaved}
          onRemove={handleHighlightSaved}
          onTagCreate={(tag) => setAllTags((prev) => [...prev, tag])}
        />
      )}
    </>
  )
}

function HighlightsPage() {
  return (
    <AuthProvider>
      <RequireAuth>
        <Layout>
          <HighlightsList />
        </Layout>
      </RequireAuth>
    </AuthProvider>
  )
}

render(<HighlightsPage />, document.getElementById('app'))
