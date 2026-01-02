import './Badge.css'
import { getTagColorClass } from '../../utils/helpers'

export default function Badge({
  children,
  variant = 'default',
  value = null,
  showIcon = true,
  className = '',
  ...props
}) {
  const variantClass = variant ? `variant-${variant}` : ''
  const colorClass = value ? getTagColorClass(value) : ''
  const combinedClassName = `badge ${variantClass} ${colorClass} ${className}`.trim()

  return (
    <span className={combinedClassName} {...props}>
      {children}
    </span>
  )
}
