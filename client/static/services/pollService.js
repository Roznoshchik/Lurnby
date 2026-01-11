/**
 * Poll Service for async task polling
 *
 * Polls an endpoint at a configurable interval until a condition is met
 * or a cancel condition triggers.
 *
 * HTTP Code Strategy:
 * - 2xx with processing complete: calls onDone
 * - 2xx with processing ongoing: continues polling
 * - 4xx (client errors): auto-cancels (unretryable)
 * - 5xx (server errors): retries up to 3 consecutive failures
 */

import { api } from "./api.js";

// Track active polls for cleanup
const activePolls = new Map()

// HTTP status codes that should never be retried
const UNRETRYABLE_CODES = [400, 401, 403, 404, 405, 409, 410, 422]

// Max consecutive 5xx errors before giving up
const MAX_CONSECUTIVE_ERRORS = 3

/**
 * Start polling an endpoint
 *
 * @param {object} config - Poll configuration
 * @param {string} config.taskName - Unique identifier for this poll task (required)
 * @param {string} config.endpoint - URL to poll (required)
 * @param {function} config.onDone - Callback when complete: (data) => void (required)
 * @param {function} [config.isDone] - Custom completion check: ({status, data}) => boolean. Defaults to status === 200
 * @param {function} [config.onProgress] - Optional callback on each poll while processing: (data) => void
 * @param {function} [config.onCancel] - Optional callback when polling is cancelled: (reason, context) => void
 * @param {function} [config.onError] - Optional callback on retryable errors: (error, context) => void
 * @param {Array<function>} [config.shouldCancel] - Array of additional cancel predicates
 * @param {number} [config.frequency=2000] - Polling interval in ms
 * @returns {function} Cancel function to stop polling
 */
export function poll(config) {
  const {
    taskName,
    endpoint,
    onDone,
    isDone = ({ status }) => status === 200,
    onProgress,
    onCancel,
    onError,
    shouldCancel = [],
    frequency = 2000,
  } = config

  // Validate required params
  if (!taskName) {
    throw new Error('pollService: taskName is required')
  }
  if (!endpoint) {
    throw new Error('pollService: endpoint is required')
  }
  if (!onDone) {
    throw new Error('pollService: onDone is required')
  }

  // Cancel any existing poll with the same name
  const existingCancel = activePolls.get(taskName)
  if (existingCancel) {
    existingCancel()
  }

  let cancelled = false
  let timeoutId = null
  let attempts = 0
  let consecutiveErrors = 0
  const startTime = Date.now()

  const createContext = () => ({
    attempts,
    consecutiveErrors,
    elapsed: Date.now() - startTime,
    taskName,
  })

  const cleanup = () => {
    cancelled = true
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
    activePolls.delete(taskName)
  }

  const cancel = (reason) => {
    const context = createContext()
    cleanup()
    if (onCancel) {
      onCancel(reason, context)
    }
  }

  const doPoll = async () => {
    if (cancelled) return

    attempts++
    const context = createContext()

    try {
      const { status, data } = await api.get(endpoint)

      if (cancelled) return

      // Reset consecutive errors on success
      consecutiveErrors = 0

      // Check if done (defaults to status === 200)
      if (isDone({ status, data })) {
        cleanup()
        onDone(data)
        return
      }

      // Still processing - call progress callback
      if (onProgress) {
        onProgress(data)
      }

      // Check user-provided cancel conditions
      for (const cancelFn of shouldCancel) {
        const cancelResult = cancelFn(data, context)
        if (cancelResult) {
          cancel(cancelResult.reason || 'Cancel condition met')
          return
        }
      }

      // Schedule next poll
      timeoutId = setTimeout(doPoll, frequency)
    } catch (error) {
      if (cancelled) return

      consecutiveErrors++
      const updatedContext = createContext()

      // Check for unretryable HTTP codes (4xx)
      if (error.status && UNRETRYABLE_CODES.includes(error.status)) {
        cancel(`HTTP ${error.status} - unretryable`)
        return
      }

      // Check for too many consecutive errors
      if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
        cancel(`${MAX_CONSECUTIVE_ERRORS} consecutive errors`)
        return
      }

      // Check user-provided cancel conditions for errors
      for (const cancelFn of shouldCancel) {
        const cancelResult = cancelFn(null, updatedContext, error)
        if (cancelResult) {
          cancel(cancelResult.reason || 'Cancel condition met')
          return
        }
      }

      // Retryable error - notify and continue
      if (onError) {
        onError(error, updatedContext)
      }
      timeoutId = setTimeout(doPoll, frequency)
    }
  }

  // Store cancel function
  activePolls.set(taskName, () => cancel('Manually cancelled'))

  // Start polling immediately
  doPoll()

  // Return cancel function
  return () => cancel('Manually cancelled')
}

/**
 * Cancel helper: Stop after N attempts
 *
 * @param {number} maxAttempts - Maximum number of poll attempts
 * @returns {function} Cancel predicate
 */
export function stopAfterAttempts(maxAttempts) {
  return (_response, context) => {
    if (context.attempts >= maxAttempts) {
      return { reason: `Max attempts (${maxAttempts}) reached` }
    }
    return false
  }
}

/**
 * Cancel helper: Stop after elapsed time
 *
 * @param {number} maxMs - Maximum time in milliseconds
 * @returns {function} Cancel predicate
 */
export function stopAfterTime(maxMs) {
  return (_response, context) => {
    if (context.elapsed >= maxMs) {
      return { reason: `Timeout (${maxMs}ms) reached` }
    }
    return false
  }
}

/**
 * Cancel helper: Stop on specific HTTP error codes (in addition to built-in unretryable codes)
 *
 * @param {Array<number>} codes - Additional HTTP status codes that should cancel polling
 * @returns {function} Cancel predicate
 */
export function stopOnErrorCodes(codes) {
  return (_response, _context, error) => {
    if (error?.status && codes.includes(error.status)) {
      return { reason: `HTTP ${error.status}` }
    }
    return false
  }
}

/**
 * Cancel helper: Custom cancel predicate
 *
 * @param {function} predicate - Custom function: (response, context, error?) => boolean | {reason: string}
 * @returns {function} Cancel predicate
 */
export function stopOnCustom(predicate) {
  return (response, context, error) => {
    const result = predicate(response, context, error)
    if (result === true) {
      return { reason: 'Custom cancel condition met' }
    }
    return result
  }
}

/**
 * Cancel all active polls
 */
export function cancelAll() {
  for (const cancel of activePolls.values()) {
    cancel()
  }
}

/**
 * Check if a poll is active
 *
 * @param {string} taskName - Task name to check
 * @returns {boolean}
 */
export function isPolling(taskName) {
  return activePolls.has(taskName)
}

// Default export with all helpers attached
const pollService = {
  poll,
  stopAfterAttempts,
  stopAfterTime,
  stopOnErrorCodes,
  stopOnCustom,
  cancelAll,
  isPolling,
}

export default pollService
