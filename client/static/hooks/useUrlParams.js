import { useState, useEffect, useCallback, useRef } from 'preact/hooks'

/**
 * Hook to sync state with URL query parameters.
 * Reads from URL on mount, writes to URL on state change.
 *
 * @param {Object} defaults - Default values for each param (also defines the schema)
 * @returns {[Object, Function]} - [params, setParams]
 *
 * @example
 * const [params, setParams] = useUrlParams({
 *   page: 1,
 *   perPage: '15',
 *   q: '',
 *   status: '',
 * })
 *
 * // Update single param
 * setParams({ page: 2 })
 *
 * // Update multiple params
 * setParams({ page: 1, status: 'unread' })
 */
export function useUrlParams(defaults) {
  const isInitialMount = useRef(true)

  // Parse URL params on mount
  const getInitialParams = () => {
    const urlParams = new URLSearchParams(window.location.search)
    const params = { ...defaults }

    for (const key of Object.keys(defaults)) {
      const urlValue = urlParams.get(key)
      if (urlValue !== null) {
        // Convert to appropriate type based on default value
        const defaultValue = defaults[key]
        if (typeof defaultValue === 'number') {
          params[key] = parseInt(urlValue, 10) || defaultValue
        } else {
          params[key] = urlValue
        }
      }
    }

    return params
  }

  const [params, setParamsState] = useState(getInitialParams)

  // Update URL when params change (but not on initial mount)
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false
      return
    }

    const urlParams = new URLSearchParams()

    for (const [key, value] of Object.entries(params)) {
      // Only include non-default, non-empty values
      if (value !== defaults[key] && value !== '' && value !== null) {
        urlParams.set(key, String(value))
      }
    }

    const search = urlParams.toString()
    const newUrl = search ? `${window.location.pathname}?${search}` : window.location.pathname

    window.history.replaceState(null, '', newUrl)
  }, [params])

  // Merge new params with existing
  const setParams = useCallback((newParams) => {
    setParamsState((prev) => ({ ...prev, ...newParams }))
  }, [])

  return [params, setParams]
}
