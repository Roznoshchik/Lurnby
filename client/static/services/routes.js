/**
 * Application Routes
 *
 * Centralized route definitions to avoid hardcoding paths throughout the app.
 */

export const ROUTES = {
  PAGES: {
    LOGIN: '/client/login',
    ARTICLES: '/client/articles',
    HIGHLIGHTS: '/client/highlights',
    REVIEW: '/client/review',
    TAGS: '/client/tags',
    SETTINGS: '/client/settings',
    // Dynamic routes
    article: (uuid) => `/client/articles/${uuid}`,
    reader: (articleUuid, { chunk = 0, offset = 0, unprocessed = false, highlight = null } = {}) => {
      if (unprocessed) {
        return highlight
          ? `/client/articles/${articleUuid}?unprocessed=1&highlight=${highlight}`
          : `/client/articles/${articleUuid}?unprocessed=1`
      }
      return `/client/articles/${articleUuid}?chunk=${chunk}&offset=${offset}`
    },
    articleHighlights: (uuid) => `/client/highlights?article=${uuid}`,
  },
  API: {
    LOGIN: '/api/auth/login',
    GOOGLE_LOGIN: '/api/auth/google',
    REFRESH: '/api/auth/refresh',
    LOGOUT: '/api/auth/logout',
    STATS: '/api/user/stats',
    ARTICLES: '/api/articles',
    HIGHLIGHTS: '/api/highlights',
    TAGS: '/api/tags',
    // Dynamic routes
    article: (uuid) => `/api/articles/${uuid}`,
    articleProcess: (uuid) => `/api/articles/${uuid}/process`,
    articleChunk: (uuid, idx) => `/api/articles/${uuid}/chunks/${idx}`,
    highlight: (uuid) => `/api/highlights/${uuid}`,
    task: (taskId) => `/api/tasks/${taskId}`,
  },
}
