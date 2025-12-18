/**
 * API Client with Token-Based Authentication
 *
 * This module handles all API communication with automatic token refresh.
 * The access token is stored privately within this module and never exposed.
 */

// Private module-level state (only place access token lives)
let _accessToken = null;

/**
 * Set the access token (internal use only)
 */
export const setAccessToken = (token) => {
  _accessToken = token;
};

/**
 * Get the current access token (for debugging only)
 */
export const getAccessToken = () => _accessToken;

/**
 * Clear the access token
 */
export const clearAccessToken = () => {
  _accessToken = null;
};

/**
 * Bootstrap authentication on app load
 * Attempts to refresh the access token using HttpOnly cookie
 *
 * @returns {Promise<{success: boolean, user?: object, error?: string}>}
 */
export async function bootstrapAuth() {
  try {
    const response = await fetch('/auth/refresh', {
      method: 'POST',
      credentials: 'include', // Send HttpOnly cookie
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      const data = await response.json();
      setAccessToken(data.access_token);
      return { success: true, user: data.user };
    }

    if (response.status === 401) {
      return { success: false, error: 'Not authenticated' };
    }

    const errorData = await response.json().catch(() => ({}));
    return { success: false, error: errorData.error || 'Authentication failed' };
  } catch (error) {
    console.error('Bootstrap auth error:', error);
    return { success: false, error: 'Network error' };
  }
}

/**
 * Fetch with automatic authentication and token refresh
 *
 * @param {string} url - API endpoint URL
 * @param {object} options - Fetch options
 * @returns {Promise<Response>}
 */
async function fetchWithAuth(url, options = {}) {
  // Add Authorization header with access token
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (_accessToken) {
    headers['Authorization'] = `Bearer ${_accessToken}`;
  }

  const fetchOptions = {
    ...options,
    headers,
    credentials: 'include', // Always include cookies for refresh token
  };

  // Make the request
  let response = await fetch(url, fetchOptions);

  // If 401, try to refresh token and retry once
  if (response.status === 401 && !options._retry) {
    console.log('Access token expired, attempting refresh...');

    const refreshResult = await bootstrapAuth();

    if (refreshResult.success) {
      console.log('Token refreshed successfully, retrying request...');
      // Retry the original request with new token
      return fetchWithAuth(url, { ...options, _retry: true });
    } else {
      console.log('Token refresh failed');
      clearAccessToken();
      // Return the 401 response so the component can handle redirect
      return response;
    }
  }

  return response;
}

/**
 * Login with username and password
 *
 * @param {string} username
 * @param {string} password
 * @returns {Promise<{success: boolean, user?: object, error?: string}>}
 */
export async function login(username, password) {
  try {
    const response = await fetch('/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    });

    if (response.ok) {
      const data = await response.json();
      setAccessToken(data.access_token);
      return { success: true, user: data.user };
    }

    const errorData = await response.json().catch(() => ({}));
    return { success: false, error: errorData.error || 'Login failed' };
  } catch (error) {
    console.error('Login error:', error);
    return { success: false, error: 'Network error' };
  }
}

/**
 * Login with Google OAuth
 *
 * @param {string} token - Google OAuth token
 * @returns {Promise<{success: boolean, user?: object, error?: string}>}
 */
export async function loginWithGoogle(token) {
  try {
    const response = await fetch('/auth/google', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ token }),
    });

    if (response.ok) {
      const data = await response.json();
      setAccessToken(data.access_token);
      return { success: true, user: data.user };
    }

    const errorData = await response.json().catch(() => ({}));
    return { success: false, error: errorData.error || 'Google login failed' };
  } catch (error) {
    console.error('Google login error:', error);
    return { success: false, error: 'Network error' };
  }
}

/**
 * Logout - revokes refresh token and clears access token
 *
 * @returns {Promise<{success: boolean}>}
 */
export async function logout() {
  try {
    await fetch('/auth/logout', {
      method: 'POST',
      credentials: 'include',
    });
    clearAccessToken();
    return { success: true };
  } catch (error) {
    console.error('Logout error:', error);
    clearAccessToken(); // Clear token even if request fails
    return { success: true }; // Always return success for logout
  }
}

/**
 * Generic API Client
 */
export const api = {
  /**
   * GET request
   * @param {string} endpoint - API endpoint (e.g., '/api/articles')
   * @param {object} params - Query parameters
   * @returns {Promise<Response>}
   */
  async get(endpoint, params = {}) {
    const queryString = Object.keys(params).length
      ? '?' + new URLSearchParams(params).toString()
      : '';
    const response = await fetchWithAuth(`${endpoint}${queryString}`);
    return response;
  },

  /**
   * POST request
   * @param {string} endpoint - API endpoint
   * @param {object} data - Request body
   * @returns {Promise<Response>}
   */
  async post(endpoint, data = {}) {
    const response = await fetchWithAuth(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response;
  },

  /**
   * PATCH request
   * @param {string} endpoint - API endpoint
   * @param {object} data - Request body
   * @returns {Promise<Response>}
   */
  async patch(endpoint, data = {}) {
    const response = await fetchWithAuth(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
    return response;
  },

  /**
   * PUT request
   * @param {string} endpoint - API endpoint
   * @param {object} data - Request body
   * @returns {Promise<Response>}
   */
  async put(endpoint, data = {}) {
    const response = await fetchWithAuth(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    return response;
  },

  /**
   * DELETE request
   * @param {string} endpoint - API endpoint
   * @returns {Promise<Response>}
   */
  async delete(endpoint) {
    const response = await fetchWithAuth(endpoint, {
      method: 'DELETE',
    });
    return response;
  },
};
