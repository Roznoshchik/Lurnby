import Icon from '../Icon/Icon'

export default function Button({
  variant = 'default',
  size,
  onClick,
  disabled = false,
  type = 'button',
  icon,
  iconVariant = 'outlined',
  iconFilled = false,
  children,
  className = '',
  ...props
}) {
  const variantClass = `btn-${variant}`
  const sizeClass = size ? `btn-${size}` : ''
  const classes = [variantClass, sizeClass, className].filter(Boolean).join(' ')

  return (
    <button type={type} className={classes} onClick={onClick} disabled={disabled} {...props}>
      {icon && <Icon name={icon} variant={iconVariant} filled={iconFilled} />}
      {children}
    </button>
  )
}
