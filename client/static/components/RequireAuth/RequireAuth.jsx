import { useAuth } from '../../contexts/AuthContext/AuthContext.jsx';
import './RequireAuth.css';

/**
 * RequireAuth Wrapper Component
 *
 * Protects routes that require authentication.
 * Redirects to login page if user is not authenticated.
 *
 * Usage:
 *   <RequireAuth>
 *     <ProtectedComponent />
 *   </RequireAuth>
 */
export default function RequireAuth({ children }) {
  const { status } = useAuth();

  // Show nothing while checking auth status
  if (status === 'loading') {
    return (
      <div className="loading-container">
        <div className="loading-text">Loading...</div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (status === 'anon') {
    const currentPath = window.location.pathname;
    const loginUrl = `/client/login?next=${encodeURIComponent(currentPath)}`;
    window.location.replace(loginUrl);
    return null;
  }

  // Render children if authenticated
  return children;
}
