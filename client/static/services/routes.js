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
    reader: (articleUuid, highlightUuid = null) =>
      highlightUuid
        ? `/client/articles/${articleUuid}?highlight=${highlightUuid}`
        : `/client/articles/${articleUuid}`,
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
    highlight: (uuid) => `/api/highlights/${uuid}`,
    task: (taskId) => `/api/tasks/${taskId}`,
  },
}
