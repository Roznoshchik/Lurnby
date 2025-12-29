import './Icon.css'

export default function Icon({ name, variant = 'outlined', filled = false, className = '' }) {
  const baseClass = `material-symbols-${variant}`
  const filledClass = filled ? 'filled' : ''
  const classes = [baseClass, filledClass, className].filter(Boolean).join(' ')

  return (
    <span className={classes} translate={false}>
      {name}
    </span>
  )
}
