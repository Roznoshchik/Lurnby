import Icon from '../Icon/Icon'
import './Select.css'

export default function Select({ options, value, onChange, placeholder, className = '' }) {
  return (
    <div className={`select-wrapper ${className}`}>
      <select className="select" value={value} onChange={(e) => onChange(e.target.value)}>
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <Icon name="expand_more" className="select-icon" />
    </div>
  )
}
