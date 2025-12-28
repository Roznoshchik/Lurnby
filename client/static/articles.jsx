import { render } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import './css/globals.css';
import './css/articles.css';
import { Layout } from './components/Layout/Layout';
import { AuthProvider } from './contexts/AuthContext/AuthContext';
import RequireAuth from './components/RequireAuth/RequireAuth';
import ArticleCard from './components/ArticleCard/ArticleCard';
import Button from './components/Button/Button';
import Icon from './components/Icon/Icon';
import { api } from './utils/api';
import { getReadableSource } from './utils/sourceFormatter';

function ArticlesList() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [monthlyStats, setMonthlyStats] = useState({
    reviewEvents: 0,
    articlesOpened: 0,
    highlightsAdded: 0,
  });

  useEffect(() => {
    fetchArticles();
    // TODO: Fetch monthly stats from /api/users/:id/stats endpoint
  }, []);

  const fetchArticles = async () => {
    try {
      setLoading(true);
      const data = await api.get('/api/articles', { per_page: 50 });
      setArticles(data.articles || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching articles:', err);
      setError('Failed to load articles');
    } finally {
      setLoading(false);
    }
  };

  const handleArticleClick = (article) => {
    // TODO: Navigate to article reader page
    console.log('Article clicked:', article);
  };

  return (
    <>
      {/* Page Header */}
      <header className="page-header">
        <div className="page-header-content">
          <div className="page-header-top">
            <div className="page-header-title">
              <Icon name="menu_book" />
              <h1>Articles</h1>
              <span className="page-header-subtitle">Your Reading Library</span>
            </div>
            <Button
              variant="default"
              icon="add"
              onClick={() => console.log('Add new article')}
            >
              Add Article
            </Button>
          </div>

          {/* Monthly Stats */}
          <div className="stats-grid">
            <div className="stat-card stat-reviews">
              <div className="stat-icon">
                <Icon name="rotate_left" />
              </div>
              <div className="stat-content">
                <div className="stat-value">{monthlyStats.reviewEvents}</div>
                <div className="stat-label">Review Events</div>
                <div className="stat-period">This Month</div>
              </div>
            </div>

            <div className="stat-card stat-articles">
              <div className="stat-icon">
                <Icon name="book" />
              </div>
              <div className="stat-content">
                <div className="stat-value">{monthlyStats.articlesOpened}</div>
                <div className="stat-label">Articles Opened</div>
                <div className="stat-period">This Month</div>
              </div>
            </div>

            <div className="stat-card stat-highlights">
              <div className="stat-icon">
                <Icon name="ink_highlighter" />
              </div>
              <div className="stat-content">
                <div className="stat-value">{monthlyStats.highlightsAdded}</div>
                <div className="stat-label">Highlights Added</div>
                <div className="stat-period">This Month</div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {loading && (
        <div className="content-container">
          <div className="loading-state">
            <p>Loading articles...</p>
          </div>
        </div>
      )}

      {error && (
        <div className="content-container">
          <div className="error-state">
            <p>{error}</p>
            <Button onClick={fetchArticles}>Retry</Button>
          </div>
        </div>
      )}

      {!loading && !error && articles.length === 0 && (
        <div className="content-container">
          <div className="empty-state">
            <Icon name="book" />
            <h3>No articles yet</h3>
            <p>Start by adding your first article!</p>
          </div>
        </div>
      )}

      {!loading && !error && articles.length > 0 && (
        <div className="content-container">
          <div className="articles-grid">
            {articles.map(article => (
              <ArticleCard
                key={article.id}
                article={{
                  ...article,
                  source: getReadableSource(article.source),
                }}
                onClick={() => handleArticleClick(article)}
              />
            ))}
          </div>
        </div>
      )}
    </>
  );
}

function ArticlesPage() {
  return (
    <AuthProvider>
      <RequireAuth>
        <Layout>
          <ArticlesList />
        </Layout>
      </RequireAuth>
    </AuthProvider>
  );
}

render(<ArticlesPage />, document.getElementById('app'));
