import { useEffect, useState, useRef, useCallback } from 'preact/hooks'
import { api } from '../services/api'
import { ROUTES } from '../services/routes'

export function useReaderProgress(contentRef, articleUuid, loading, initialProgress = 0) {
  const [progress, setProgress] = useState(initialProgress)
  const saveTimeoutRef = useRef(null)

  // Reset progress when article changes
  useEffect(() => {
    setProgress(initialProgress)
  }, [initialProgress])

  const saveProgress = useCallback(
    (newProgress) => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }

      saveTimeoutRef.current = setTimeout(async () => {
        try {
          await api.patch(ROUTES.API.article(articleUuid), {
            progress: newProgress,
            done: newProgress >= 100,
          })
        } catch (err) {
          console.error('Error saving progress:', err)
        }
      }, 2000)
    },
    [articleUuid],
  )

  // Scroll tracking
  useEffect(() => {
    const container = contentRef.current?.contentContainer
    if (!container || loading) return

    const handleScroll = () => {
      const scrollTop = container.scrollTop
      const scrollHeight = container.scrollHeight - container.clientHeight
      const scrollPercent = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0
      const newProgress = Math.min(100, Math.max(0, scrollPercent))

      setProgress(newProgress)
      saveProgress(newProgress)
    }

    container.addEventListener('scroll', handleScroll, { passive: true })
    return () => container.removeEventListener('scroll', handleScroll)
  }, [contentRef, articleUuid, loading, saveProgress])

  return { progress }
}
