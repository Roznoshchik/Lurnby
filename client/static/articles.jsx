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

  useEffect(() => {
    fetchArticles();
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

  if (loading) {
    return (
      <div className="content-container">
        <div className="loading-state">
          <p>Loading articles...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="content-container">
        <div className="error-state">
          <p>{error}</p>
          <Button onClick={fetchArticles}>Retry</Button>
        </div>
      </div>
    );
  }

  if (articles.length === 0) {
    return (
      <div className="content-container">
        <div className="empty-state">
          <Icon name="book" />
          <h3>No articles yet</h3>
          <p>Start by adding your first article!</p>
        </div>
      </div>
    );
  }

  return (
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
