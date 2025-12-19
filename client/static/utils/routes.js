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
  },
  API: {
    LOGIN: '/api/auth/login',
    GOOGLE_LOGIN: '/api/auth/google',
    REFRESH: '/api/auth/refresh',
    LOGOUT: '/api/auth/logout',
  },
};
