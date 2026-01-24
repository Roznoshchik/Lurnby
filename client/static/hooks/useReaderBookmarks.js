import { useEffect, useRef, useCallback } from 'preact/hooks'
import { api } from '../services/api'
import { ROUTES } from '../services/routes'

export function useReaderBookmarks(
  contentRef,
  articleUuid,
  loading,
  hasContentTree,
  bookmarks,
  setArticle,
) {
  const furthestRef = useRef(0)
  const bookmarksRef = useRef([])

  // Keep refs in sync with bookmarks prop
  useEffect(() => {
    bookmarksRef.current = bookmarks || []
    const furthest = bookmarks?.find((b) => b.name === 'furthest')
    furthestRef.current = furthest?.start || 0
  }, [bookmarks])

  const saveBookmarks = useCallback(
    async (newBookmarks) => {
      try {
        await api.patch(ROUTES.API.article(articleUuid), {
          bookmarks: JSON.stringify(newBookmarks),
        })
      } catch (err) {
        console.error('Error saving bookmarks:', err)
      }
    },
    [articleUuid],
  )

  const addBookmark = useCallback(
    (name) => {
      if (!name) return false

      const start = contentRef.current?.getReaderLocation()
      if (start == null) return false

      const current = bookmarksRef.current
      const newBookmarks = [
        ...current.filter((b) => b.name !== name),
        { name, start, legacy: null },
      ]

      setArticle((prev) => ({ ...prev, bookmarks: newBookmarks }))
      saveBookmarks(newBookmarks)
      return true
    },
    [contentRef, setArticle, saveBookmarks],
  )

  const deleteBookmark = useCallback(
    (name) => {
      const current = bookmarksRef.current
      const newBookmarks = current.filter((b) => b.name !== name)
      setArticle((prev) => ({ ...prev, bookmarks: newBookmarks }))
      saveBookmarks(newBookmarks)
    },
    [setArticle, saveBookmarks],
  )

  const updateBookmark = useCallback(
    (name, start) => {
      const current = bookmarksRef.current
      const newBookmarks = current.map((b) => (b.name === name ? { ...b, start, legacy: null } : b))
      setArticle((prev) => ({ ...prev, bookmarks: newBookmarks }))
      saveBookmarks(newBookmarks)
    },
    [setArticle, saveBookmarks],
  )

  const resetFurthest = useCallback(() => {
    const location = contentRef.current?.getReaderLocation()
    if (location == null) return

    furthestRef.current = location
    const current = bookmarksRef.current
    const withoutFurthest = current.filter((b) => b.name !== 'furthest')
    const newBookmarks = [...withoutFurthest, { name: 'furthest', start: location, legacy: null }]
    setArticle((prev) => ({ ...prev, bookmarks: newBookmarks }))
    saveBookmarks(newBookmarks)
  }, [contentRef, setArticle, saveBookmarks])

  // TODO: Once all legacy bookmarks are migrated (check db), remove legacy migration
  const jumpToBookmark = useCallback(
    (bookmark) => {
      // For furthest, use the ref (which is current) not the stale article state
      const target =
        bookmark.name === 'furthest' ? { ...bookmark, start: furthestRef.current } : bookmark

      const jumped = contentRef.current?.jumpToBookmark(target)

      // After legacy jump, migrate to offset-based
      if (jumped && bookmark.legacy != null) {
        setTimeout(() => {
          const location = contentRef.current?.getReaderLocation()
          if (location != null) {
            updateBookmark(bookmark.name, location)
          }
        }, 500)
      }
    },
    [contentRef, updateBookmark],
  )

  // Track furthest read position on scroll
  useEffect(() => {
    const container = contentRef.current?.contentContainer
    if (!container || loading || !hasContentTree) return

    let debounceTimer = null

    const handleScroll = () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        const location = contentRef.current?.getReaderLocation()
        if (location == null) return
        if (location <= furthestRef.current) return

        furthestRef.current = location
        const current = bookmarksRef.current || []
        const withoutFurthest = current.filter((b) => b.name !== 'furthest')
        const newBookmarks = [
          ...withoutFurthest,
          { name: 'furthest', start: location, legacy: null },
        ]
        saveBookmarks(newBookmarks)
      }, 500)
    }

    container.addEventListener('scroll', handleScroll, { passive: true })
    return () => {
      container.removeEventListener('scroll', handleScroll)
      if (debounceTimer) clearTimeout(debounceTimer)
    }
  }, [contentRef, articleUuid, loading, hasContentTree, saveBookmarks])

  // Derived values for UI
  const furthestBookmark = bookmarks?.find((b) => b.name === 'furthest')
  const userBookmarks = bookmarks?.filter((b) => b.name !== 'furthest') || []

  return {
    addBookmark,
    deleteBookmark,
    jumpToBookmark,
    resetFurthest,
    furthestBookmark,
    userBookmarks,
  }
}
