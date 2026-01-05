import './Card.css'

export default function Card({
  children,
  variant = 'default',
  padding = 'md',
  interactive = false,
  onClick,
  className = '',
  as: Component = 'div',
  ...props
}) {
  const classNames = [
    'card',
    `card-${variant}`,
    `card-padding-${padding}`,
    interactive && 'card-interactive',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <Component className={classNames} onClick={onClick} {...props}>
      {children}
    </Component>
  )
}
