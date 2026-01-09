import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import {
  poll,
  stopAfterAttempts,
  stopAfterTime,
  stopOnErrorCodes,
  stopOnCustom,
  cancelAll,
  isPolling,
} from './pollService.js'

// Mock the api module
vi.mock('../utils/api.js', () => ({
  api: {
    get: vi.fn(),
  },
}))

import { api } from '../utils/api.js'

describe('pollService', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
    cancelAll()
  })

  afterEach(() => {
    vi.useRealTimers()
    cancelAll()
  })

  describe('poll', () => {
    it('throws if required params are missing', () => {
      expect(() => poll({})).toThrow('taskName is required')
      expect(() => poll({ taskName: 'test' })).toThrow('endpoint is required')
      expect(() => poll({ taskName: 'test', endpoint: '/api/task' })).toThrow('onDone is required')
      expect(() =>
        poll({ taskName: 'test', endpoint: '/api/task', onDone: () => {} }),
      ).toThrow('isDone is required')
    })

    it('calls onDone when isDone returns true', async () => {
      const onDone = vi.fn()
      api.get.mockResolvedValue({ status: 'complete' })

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone,
        isDone: (res) => res.status === 'complete',
      })

      await vi.runAllTimersAsync()

      expect(onDone).toHaveBeenCalledWith({ status: 'complete' })
      expect(api.get).toHaveBeenCalledWith('/api/task/123')
    })

    it('continues polling when isDone returns false', async () => {
      const onDone = vi.fn()
      const onProgress = vi.fn()
      let callCount = 0

      api.get.mockImplementation(() => {
        callCount++
        if (callCount >= 3) {
          return Promise.resolve({ status: 'complete' })
        }
        return Promise.resolve({ status: 'processing', progress: callCount * 30 })
      })

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone,
        onProgress,
        isDone: (res) => res.status === 'complete',
        frequency: 1000,
      })

      // First poll (immediate)
      await vi.advanceTimersByTimeAsync(0)
      expect(onProgress).toHaveBeenCalledWith({ status: 'processing', progress: 30 })

      // Second poll
      await vi.advanceTimersByTimeAsync(1000)
      expect(onProgress).toHaveBeenCalledWith({ status: 'processing', progress: 60 })

      // Third poll - completes
      await vi.advanceTimersByTimeAsync(1000)
      expect(onDone).toHaveBeenCalledWith({ status: 'complete' })
      expect(api.get).toHaveBeenCalledTimes(3)
    })

    it('cancels existing poll with same taskName', async () => {
      const onCancel = vi.fn()
      api.get.mockResolvedValue({ status: 'processing' })

      poll({
        taskName: 'same-task',
        endpoint: '/api/task/1',
        onDone: () => {},
        onCancel,
        isDone: () => false,
      })

      // Start second poll with same name
      poll({
        taskName: 'same-task',
        endpoint: '/api/task/2',
        onDone: () => {},
        isDone: () => false,
      })

      expect(onCancel).toHaveBeenCalledWith('Manually cancelled', expect.any(Object))
    })

    it('returns cancel function that stops polling', async () => {
      const onCancel = vi.fn()
      api.get.mockResolvedValue({ status: 'processing' })

      const cancel = poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone: () => {},
        onCancel,
        isDone: () => false,
        frequency: 1000,
      })

      await vi.advanceTimersByTimeAsync(0)
      expect(api.get).toHaveBeenCalledTimes(1)

      cancel()

      await vi.advanceTimersByTimeAsync(5000)
      expect(api.get).toHaveBeenCalledTimes(1) // No more calls after cancel
      expect(onCancel).toHaveBeenCalledWith('Manually cancelled', expect.any(Object))
    })

    it('auto-cancels on 4xx errors', async () => {
      const onCancel = vi.fn()
      const error = new Error('HTTP 404: Not Found')
      error.status = 404
      api.get.mockRejectedValue(error)

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone: () => {},
        onCancel,
        isDone: () => false,
      })

      await vi.runAllTimersAsync()

      expect(onCancel).toHaveBeenCalledWith('HTTP 404 - unretryable', expect.any(Object))
    })

    it('retries on 5xx errors up to MAX_CONSECUTIVE_ERRORS', async () => {
      const onCancel = vi.fn()
      const onError = vi.fn()
      const error = new Error('HTTP 500: Internal Server Error')
      error.status = 500
      api.get.mockRejectedValue(error)

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone: () => {},
        onCancel,
        onError,
        isDone: () => false,
        frequency: 1000,
      })

      // First error
      await vi.advanceTimersByTimeAsync(0)
      expect(onError).toHaveBeenCalledTimes(1)

      // Second error
      await vi.advanceTimersByTimeAsync(1000)
      expect(onError).toHaveBeenCalledTimes(2)

      // Third error - should cancel
      await vi.advanceTimersByTimeAsync(1000)
      expect(onCancel).toHaveBeenCalledWith('3 consecutive errors', expect.any(Object))
    })

    it('resets consecutive errors on success', async () => {
      const onDone = vi.fn()
      let callCount = 0

      api.get.mockImplementation(() => {
        callCount++
        if (callCount === 1 || callCount === 2) {
          const error = new Error('HTTP 500: Error')
          error.status = 500
          return Promise.reject(error)
        }
        if (callCount === 3 || callCount === 4) {
          return Promise.resolve({ status: 'processing' })
        }
        return Promise.resolve({ status: 'complete' })
      })

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone,
        isDone: (res) => res.status === 'complete',
        frequency: 1000,
      })

      // 2 errors, then success, should continue
      await vi.advanceTimersByTimeAsync(0) // error 1
      await vi.advanceTimersByTimeAsync(1000) // error 2
      await vi.advanceTimersByTimeAsync(1000) // success (resets counter)
      await vi.advanceTimersByTimeAsync(1000) // success
      await vi.advanceTimersByTimeAsync(1000) // complete

      expect(onDone).toHaveBeenCalledWith({ status: 'complete' })
    })
  })

  describe('stopAfterAttempts', () => {
    it('cancels after max attempts', async () => {
      const onCancel = vi.fn()
      api.get.mockResolvedValue({ status: 'processing' })

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone: () => {},
        onCancel,
        isDone: () => false,
        shouldCancel: [stopAfterAttempts(3)],
        frequency: 1000,
      })

      await vi.advanceTimersByTimeAsync(0) // attempt 1
      await vi.advanceTimersByTimeAsync(1000) // attempt 2
      await vi.advanceTimersByTimeAsync(1000) // attempt 3 - should cancel

      expect(onCancel).toHaveBeenCalledWith('Max attempts (3) reached', expect.any(Object))
      expect(api.get).toHaveBeenCalledTimes(3)
    })
  })

  describe('stopAfterTime', () => {
    it('cancels after elapsed time', async () => {
      const onCancel = vi.fn()
      api.get.mockResolvedValue({ status: 'processing' })

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone: () => {},
        onCancel,
        isDone: () => false,
        shouldCancel: [stopAfterTime(2500)],
        frequency: 1000,
      })

      await vi.advanceTimersByTimeAsync(0) // 0ms
      await vi.advanceTimersByTimeAsync(1000) // 1000ms
      await vi.advanceTimersByTimeAsync(1000) // 2000ms
      await vi.advanceTimersByTimeAsync(1000) // 3000ms - should cancel

      expect(onCancel).toHaveBeenCalledWith('Timeout (2500ms) reached', expect.any(Object))
    })
  })

  describe('stopOnErrorCodes', () => {
    it('cancels on specified error codes', async () => {
      const onCancel = vi.fn()
      const error = new Error('HTTP 503: Service Unavailable')
      error.status = 503
      api.get.mockRejectedValue(error)

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone: () => {},
        onCancel,
        isDone: () => false,
        shouldCancel: [stopOnErrorCodes([502, 503, 504])],
      })

      await vi.runAllTimersAsync()

      expect(onCancel).toHaveBeenCalledWith('HTTP 503', expect.any(Object))
    })
  })

  describe('stopOnCustom', () => {
    it('cancels when custom predicate returns true', async () => {
      const onCancel = vi.fn()
      api.get.mockResolvedValue({ status: 'failed', error: 'Something broke' })

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone: () => {},
        onCancel,
        isDone: () => false,
        shouldCancel: [stopOnCustom((res) => res?.status === 'failed')],
      })

      await vi.runAllTimersAsync()

      expect(onCancel).toHaveBeenCalledWith('Custom cancel condition met', expect.any(Object))
    })

    it('cancels when custom predicate returns object with reason', async () => {
      const onCancel = vi.fn()
      api.get.mockResolvedValue({ status: 'failed', error: 'Disk full' })

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone: () => {},
        onCancel,
        isDone: () => false,
        shouldCancel: [
          stopOnCustom((res) => {
            if (res?.status === 'failed') {
              return { reason: `Task failed: ${res.error}` }
            }
            return false
          }),
        ],
      })

      await vi.runAllTimersAsync()

      expect(onCancel).toHaveBeenCalledWith('Task failed: Disk full', expect.any(Object))
    })
  })

  describe('isPolling', () => {
    it('returns true for active polls', () => {
      api.get.mockResolvedValue({ status: 'processing' })

      poll({
        taskName: 'active-poll',
        endpoint: '/api/task/123',
        onDone: () => {},
        isDone: () => false,
      })

      expect(isPolling('active-poll')).toBe(true)
      expect(isPolling('other-poll')).toBe(false)
    })

    it('returns false after poll completes', async () => {
      api.get.mockResolvedValue({ status: 'complete' })

      poll({
        taskName: 'completed-poll',
        endpoint: '/api/task/123',
        onDone: () => {},
        isDone: () => true,
      })

      await vi.runAllTimersAsync()

      expect(isPolling('completed-poll')).toBe(false)
    })
  })

  describe('cancelAll', () => {
    it('cancels all active polls', async () => {
      const onCancel1 = vi.fn()
      const onCancel2 = vi.fn()
      api.get.mockResolvedValue({ status: 'processing' })

      poll({
        taskName: 'poll-1',
        endpoint: '/api/task/1',
        onDone: () => {},
        onCancel: onCancel1,
        isDone: () => false,
      })

      poll({
        taskName: 'poll-2',
        endpoint: '/api/task/2',
        onDone: () => {},
        onCancel: onCancel2,
        isDone: () => false,
      })

      cancelAll()

      expect(onCancel1).toHaveBeenCalled()
      expect(onCancel2).toHaveBeenCalled()
      expect(isPolling('poll-1')).toBe(false)
      expect(isPolling('poll-2')).toBe(false)
    })
  })
})
