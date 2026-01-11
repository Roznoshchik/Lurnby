/**
 * Alert Service - wraps sonner toast with app-specific defaults
 */

import { toast } from 'sonner'

const DEFAULT_DURATION = 4000

/**
 * Show a success alert
 * @param {string} message - The message to display
 * @param {object} options - Optional settings
 * @param {string} options.description - Additional description text
 * @param {number|null} options.duration - Duration in ms (null for persistent)
 */
export function success(message, options = {}) {
  const { description, duration = DEFAULT_DURATION } = options
  toast.success(message, {
    description,
    duration: duration === null ? Infinity : duration,
  })
}

/**
 * Show an error alert
 * @param {string} message - The message to display
 * @param {object} options - Optional settings
 * @param {string} options.description - Additional description text
 * @param {number|null} options.duration - Duration in ms (null for persistent)
 */
export function error(message, options = {}) {
  const { description, duration = DEFAULT_DURATION } = options
  toast.error(message, {
    description,
    duration: duration === null ? Infinity : duration,
  })
}

/**
 * Show an info alert
 * @param {string} message - The message to display
 * @param {object} options - Optional settings
 * @param {string} options.description - Additional description text
 * @param {number|null} options.duration - Duration in ms (null for persistent)
 */
export function info(message, options = {}) {
  const { description, duration = DEFAULT_DURATION } = options
  toast.info(message, {
    description,
    duration: duration === null ? Infinity : duration,
  })
}

/**
 * Show a warning alert
 * @param {string} message - The message to display
 * @param {object} options - Optional settings
 * @param {string} options.description - Additional description text
 * @param {number|null} options.duration - Duration in ms (null for persistent)
 */
export function warning(message, options = {}) {
  const { description, duration = DEFAULT_DURATION } = options
  toast.warning(message, {
    description,
    duration: duration === null ? Infinity : duration,
  })
}

/**
 * Dismiss a specific toast or all toasts
 * @param {string|number} [toastId] - Optional toast ID to dismiss (dismisses all if not provided)
 */
export function dismiss(toastId) {
  toast.dismiss(toastId)
}

const alert = {
  success,
  error,
  info,
  warning,
  dismiss,
}

export default alert
