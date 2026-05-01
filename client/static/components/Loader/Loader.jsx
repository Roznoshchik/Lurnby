import './Loader.css'

/**
 * Loader component with three modes:
 * - inline: small spinner, no wrapper (for buttons)
 * - overlay: semi-transparent cover over children
 * - card: replaces children entirely when loading
 */
export default function Loader({ isLoading, mode = 'card', text, className = '', children }) {
  const spinner = (
    <span className="loader-spinner" aria-hidden="true" />
  )

  // Inline mode: just return spinner when loading, nothing otherwise
  if (mode === 'inline') {
    return isLoading ? (
      <span className={`loader loader-inline ${className}`}>
        {spinner}
        {text && <span className="loader-text">{text}</span>}
      </span>
    ) : null
  }

  // Card mode: show loader OR children, not both
  if (mode === 'card') {
    if (isLoading) {
      return (
        <div className={`loader loader-card ${className}`}>
          {spinner}
          {text && <span className="loader-text">{text}</span>}
        </div>
      )
    }
    return children
  }

  // Overlay mode: show children with loader on top
  if (mode === 'overlay') {
    return (
      <div className={`loader-overlay-wrapper ${className}`}>
        {children}
        {isLoading && (
          <div className="loader loader-overlay">
            {spinner}
            {text && <span className="loader-text">{text}</span>}
          </div>
        )}
      </div>
    )
  }

  return children
}
