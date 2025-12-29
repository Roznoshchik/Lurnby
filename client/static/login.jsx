import { render } from 'preact'
import './style.css'
import ErrorBoundary from './components/ErrorBoundary/ErrorBoundary'
import Login from './components/Login/Login'

function App() {
  return (
    <ErrorBoundary>
      <Login />
    </ErrorBoundary>
  )
}

render(<App />, document.getElementById('app'))
