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
    })

    it('calls onDone when status is 200 (default isDone)', async () => {
      const onDone = vi.fn()
      api.get.mockResolvedValue({ status: 200, data: { result: 'complete' } })

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone,
      })

      await vi.runAllTimersAsync()

      expect(onDone).toHaveBeenCalledWith({ result: 'complete' })
      expect(api.get).toHaveBeenCalledWith('/api/task/123')
    })

    it('calls onDone when custom isDone returns true', async () => {
      const onDone = vi.fn()
      api.get.mockResolvedValue({ status: 202, data: { customField: 'done' } })

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone,
        isDone: ({ data }) => data.customField === 'done',
      })

      await vi.runAllTimersAsync()

      expect(onDone).toHaveBeenCalledWith({ customField: 'done' })
    })

    it('continues polling when status is 202', async () => {
      const onDone = vi.fn()
      const onProgress = vi.fn()
      let callCount = 0

      api.get.mockImplementation(() => {
        callCount++
        if (callCount >= 3) {
          return Promise.resolve({ status: 200, data: { result: 'complete' } })
        }
        return Promise.resolve({ status: 202, data: { progress: callCount * 30 } })
      })

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone,
        onProgress,
        frequency: 1000,
      })

      // First poll (immediate) - 202
      await vi.advanceTimersByTimeAsync(0)
      expect(onProgress).toHaveBeenCalledWith({ progress: 30 })

      // Second poll - 202
      await vi.advanceTimersByTimeAsync(1000)
      expect(onProgress).toHaveBeenCalledWith({ progress: 60 })

      // Third poll - 200 completes
      await vi.advanceTimersByTimeAsync(1000)
      expect(onDone).toHaveBeenCalledWith({ result: 'complete' })
      expect(api.get).toHaveBeenCalledTimes(3)
    })

    it('cancels existing poll with same taskName', async () => {
      const onCancel = vi.fn()
      api.get.mockResolvedValue({ status: 202, data: { processing: true } })

      poll({
        taskName: 'same-task',
        endpoint: '/api/task/1',
        onDone: () => {},
        onCancel,
        isDone: ({ status }) => status === 200,
      })

      // Start second poll with same name
      poll({
        taskName: 'same-task',
        endpoint: '/api/task/2',
        onDone: () => {},
        isDone: ({ status }) => status === 200,
      })

      expect(onCancel).toHaveBeenCalledWith('Manually cancelled', expect.any(Object))
    })

    it('returns cancel function that stops polling', async () => {
      const onCancel = vi.fn()
      api.get.mockResolvedValue({ status: 202, data: { processing: true } })

      const cancel = poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone: () => {},
        onCancel,
        isDone: ({ status }) => status === 200,
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
        isDone: ({ status }) => status === 200,
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
        isDone: ({ status }) => status === 200,
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
          return Promise.resolve({ status: 202, data: { processing: true } })
        }
        return Promise.resolve({ status: 200, data: { result: 'complete' } })
      })

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone,
        isDone: ({ status }) => status === 200,
        frequency: 1000,
      })

      // 2 errors, then success, should continue
      await vi.advanceTimersByTimeAsync(0) // error 1
      await vi.advanceTimersByTimeAsync(1000) // error 2
      await vi.advanceTimersByTimeAsync(1000) // 202 success (resets counter)
      await vi.advanceTimersByTimeAsync(1000) // 202 success
      await vi.advanceTimersByTimeAsync(1000) // 200 complete

      expect(onDone).toHaveBeenCalledWith({ result: 'complete' })
    })
  })

  describe('stopAfterAttempts', () => {
    it('cancels after max attempts', async () => {
      const onCancel = vi.fn()
      api.get.mockResolvedValue({ status: 202, data: { processing: true } })

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone: () => {},
        onCancel,
        isDone: ({ status }) => status === 200,
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
      api.get.mockResolvedValue({ status: 202, data: { processing: true } })

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone: () => {},
        onCancel,
        isDone: ({ status }) => status === 200,
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
        isDone: ({ status }) => status === 200,
        shouldCancel: [stopOnErrorCodes([502, 503, 504])],
      })

      await vi.runAllTimersAsync()

      expect(onCancel).toHaveBeenCalledWith('HTTP 503', expect.any(Object))
    })
  })

  describe('stopOnCustom', () => {
    it('cancels when custom predicate returns true', async () => {
      const onCancel = vi.fn()
      api.get.mockResolvedValue({
        status: 202,
        data: { taskStatus: 'failed', error: 'Something broke' },
      })

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone: () => {},
        onCancel,
        isDone: ({ status }) => status === 200,
        shouldCancel: [stopOnCustom((data) => data?.taskStatus === 'failed')],
      })

      await vi.runAllTimersAsync()

      expect(onCancel).toHaveBeenCalledWith('Custom cancel condition met', expect.any(Object))
    })

    it('cancels when custom predicate returns object with reason', async () => {
      const onCancel = vi.fn()
      api.get.mockResolvedValue({ status: 202, data: { taskStatus: 'failed', error: 'Disk full' } })

      poll({
        taskName: 'test',
        endpoint: '/api/task/123',
        onDone: () => {},
        onCancel,
        isDone: ({ status }) => status === 200,
        shouldCancel: [
          stopOnCustom((data) => {
            if (data?.taskStatus === 'failed') {
              return { reason: `Task failed: ${data.error}` }
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
      api.get.mockResolvedValue({ status: 202, data: { processing: true } })

      poll({
        taskName: 'active-poll',
        endpoint: '/api/task/123',
        onDone: () => {},
        isDone: ({ status }) => status === 200,
      })

      expect(isPolling('active-poll')).toBe(true)
      expect(isPolling('other-poll')).toBe(false)
    })

    it('returns false after poll completes', async () => {
      api.get.mockResolvedValue({ status: 200, data: { result: 'complete' } })

      poll({
        taskName: 'completed-poll',
        endpoint: '/api/task/123',
        onDone: () => {},
        isDone: ({ status }) => status === 200,
      })

      await vi.runAllTimersAsync()

      expect(isPolling('completed-poll')).toBe(false)
    })
  })

  describe('cancelAll', () => {
    it('cancels all active polls', async () => {
      const onCancel1 = vi.fn()
      const onCancel2 = vi.fn()
      api.get.mockResolvedValue({ status: 202, data: { processing: true } })

      poll({
        taskName: 'poll-1',
        endpoint: '/api/task/1',
        onDone: () => {},
        onCancel: onCancel1,
        isDone: ({ status }) => status === 200,
      })

      poll({
        taskName: 'poll-2',
        endpoint: '/api/task/2',
        onDone: () => {},
        onCancel: onCancel2,
        isDone: ({ status }) => status === 200,
      })

      cancelAll()

      expect(onCancel1).toHaveBeenCalled()
      expect(onCancel2).toHaveBeenCalled()
      expect(isPolling('poll-1')).toBe(false)
      expect(isPolling('poll-2')).toBe(false)
    })
  })
})
