import './Badge.css'

// Simple hash function to convert string to number
function hashString(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = (hash << 5) - hash + char
    hash = hash & hash // Convert to 32-bit integer
  }
  return Math.abs(hash)
}

// Total number of tag colors defined in CSS
const TAG_COLOR_COUNT = 9

export default function Badge({
  children,
  variant = 'default',
  value = null,
  showIcon = true,
  className = '',
  ...props
}) {
  const variantClass = variant ? `variant-${variant}` : ''

  // Compute tag color index if value is provided
  let colorClass = ''
  if (value) {
    const hash = hashString(value.toLowerCase())
    const colorIndex = hash % TAG_COLOR_COUNT
    colorClass = `tag-color-${colorIndex}`
  }

  const combinedClassName = `badge ${variantClass} ${colorClass} ${className}`.trim()

  return (
    <span className={combinedClassName} {...props}>
      {children}
    </span>
  )
}
