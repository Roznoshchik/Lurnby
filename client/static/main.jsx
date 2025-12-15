import { render } from 'preact';
import './style.css';

function App() {
  return (
    <div>
      <h1>Lurnby</h1>
      <p>Preact frontend is running!</p>
    </div>
  );
}

render(<App />, document.getElementById('app'));
