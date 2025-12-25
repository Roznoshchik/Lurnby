import { render } from 'preact';
import { Layout } from './components/Layout/Layout';
import './css/globals.css';

function ArticlesPage() {
  return (
    <Layout>
      <h1>Hello World</h1>
      <p>Articles page is working!</p>
    </Layout>
  );
}

render(<ArticlesPage />, document.getElementById('app'));
