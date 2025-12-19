import { useState } from 'preact/hooks';
import { login } from '../../utils/api';
import { ROUTES } from '../../utils/routes';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(username, password);

    if (result.success) {
      // Get the 'next' parameter from URL, or default to articles page
      const urlParams = new URLSearchParams(window.location.search);
      const next = urlParams.get('next') || ROUTES.PAGES.ARTICLES;
      window.location.href = next;
    } else {
      setError(result.error || 'Login failed');
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Login to Lurnby</h1>

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="username">Username:</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={loading}
          />
        </div>

        <div>
          <label htmlFor="password">Password:</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
          />
        </div>

        {error && <div style={{ color: 'red' }}>{error}</div>}

        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
}
