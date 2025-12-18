import { createContext } from 'preact';
import { useContext, useState, useEffect } from 'preact/hooks';
import { bootstrapAuth, logout as apiLogout } from '../utils/api.js';

/**
 * Auth Context
 *
 * Provides authentication state to the entire app.
 * Does NOT store the access token (that lives in api.js)
 *
 * State:
 * - status: 'loading' | 'authed' | 'anon'
 * - user: User object or null
 */

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [status, setStatus] = useState('loading');
  const [user, setUser] = useState(null);

  // Bootstrap auth on mount
  useEffect(() => {
    bootstrapAuth().then((result) => {
      if (result.success) {
        setUser(result.user);
        setStatus('authed');
      } else {
        setStatus('anon');
      }
    });
  }, []);

  /**
   * Set authenticated user (called after login)
   */
  const setAuthUser = (user) => {
    setUser(user);
    setStatus('authed');
  };

  /**
   * Logout user
   */
  const logout = async () => {
    await apiLogout();
    setUser(null);
    setStatus('anon');
    window.location.href = '/client/login';
  };

  const value = {
    status,
    user,
    isAuthenticated: status === 'authed',
    isLoading: status === 'loading',
    setAuthUser,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access auth context
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
