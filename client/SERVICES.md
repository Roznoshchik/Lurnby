# Frontend Services

Utility services for cross-cutting concerns. Located in `client/static/services/`.

For full API documentation, see the JSDoc comments in each service file.

## Adding a New Service

1. Create `client/static/services/myService.js`
2. Export named functions and/or a default object with methods
3. Add documentation to this file

---

## alertService

Toast notification wrapper for [Sonner](https://sonner.emilkowal.ski/).

```js
import alert from '../services/alertService'

alert.success('Article saved!')
alert.error('Failed to load', { description: 'Check your connection' })
alert.warning('Processing may take a while')
alert.info('Tip: You can swipe to dismiss')
```

**Methods:**
- `success(message, options?)` - Green success toast
- `error(message, options?)` - Red error toast
- `warning(message, options?)` - Yellow warning toast
- `info(message, options?)` - Blue info toast

**Options:**
- `description`: Secondary text below the message
- `duration`: Auto-dismiss time in ms (default: 4000). Use `null` for persistent toast.

---

## pollService

Polls an endpoint at intervals until a condition is met or cancelled.

```js
import { poll, stopAfterAttempts, stopAfterTime } from '../services/pollService'

const cancel = poll({
  taskName: 'article-123',
  endpoint: `/api/tasks/${taskId}`,
  onDone: (data) => console.log('Complete!', data),
  onProgress: (data) => console.log(`Progress: ${data.progress}%`),
  onCancel: (reason) => console.log('Cancelled:', reason),
  shouldCancel: [
    stopAfterAttempts(30),
    stopAfterTime(60000),
  ],
  frequency: 2000,
})

// Manual cancel
cancel()
```

**Required Config:**
- `taskName`: Unique identifier (cancels previous poll with same name)
- `endpoint`: URL to poll
- `onDone`: Callback when complete

**Optional Config:**
- `isDone`: Completion check function. Default: `({ status }) => status === 200`
- `onProgress`: Called each poll while processing
- `onCancel`: Called when polling stops before completion
- `onError`: Called on retryable errors
- `shouldCancel`: Array of cancel predicates
- `frequency`: Poll interval in ms (default: 2000)

**Cancel Helpers:**
- `stopAfterAttempts(n)` - Cancel after n poll attempts
- `stopAfterTime(ms)` - Cancel after elapsed time
- `stopOnErrorCodes([codes])` - Cancel on specific HTTP errors
- `stopOnCustom(predicate)` - Custom cancel logic

**Utilities:**
- `cancelAll()` - Cancel all active polls
- `isPolling(taskName)` - Check if a poll is active
