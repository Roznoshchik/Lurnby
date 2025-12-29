import { Component } from 'preact'
import './ErrorBoundary.css'

/**
 * Error Boundary Component
 *
 * Catches JavaScript errors in child components and displays a fallback UI.
 * Prevents the entire app from crashing due to errors in specific components.
 *
 * Usage:
 *   <ErrorBoundary>
 *     <Component />
 *   </ErrorBoundary>
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(_error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to console
    console.error('ErrorBoundary caught an error:', error, errorInfo)

    // Update state with error details
    this.setState({
      error,
      errorInfo,
    })
  }

  render() {
    if (this.state.hasError) {
      // Fallback UI
      return (
        <div className="error-boundary-container">
          <h2 className="error-boundary-title">Something went wrong</h2>
          <p className="error-boundary-message">
            We're sorry for the inconvenience. Please try refreshing the page.
          </p>

          <button
            type="button"
            onClick={() => window.location.reload()}
            className="error-boundary-button"
          >
            Refresh Page
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
