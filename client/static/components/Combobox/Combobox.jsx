import { useState, useRef, useEffect, useMemo } from 'preact/hooks'
import Button from '../Button/Button'
import Icon from '../Icon/Icon'
import { getTagColorClass } from '../../utils/helpers'
import './Combobox.css'

export default function Combobox({ options, selected, onSelect, placeholder = 'Select...' }) {
  const [open, setOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [highlightedIndex, setHighlightedIndex] = useState(0)
  const containerRef = useRef(null)
  const inputRef = useRef(null)
  const optionsRef = useRef(null)

  // Focus input when dropdown opens
  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus()
    }
  }, [open])

  // Reset highlighted index when filtered options change
  useEffect(() => {
    setHighlightedIndex(0)
  }, [searchQuery])

  // Scroll highlighted option into view
  useEffect(() => {
    if (optionsRef.current && open) {
      const highlighted = optionsRef.current.children[highlightedIndex]
      if (highlighted) {
        highlighted.scrollIntoView({ block: 'nearest' })
      }
    }
  }, [highlightedIndex, open])

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false)
      }
    }

    if (open) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [open])

  const filteredOptions = useMemo(() => {
    if (!searchQuery) return options
    return options.filter((option) => option.label.toLowerCase().includes(searchQuery.toLowerCase()))
  }, [options, searchQuery])

  const handleKeyDown = (e) => {
    if (!open) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex((prev) => (prev < filteredOptions.length - 1 ? prev + 1 : 0))
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : filteredOptions.length - 1))
        break
      case 'Enter':
      case ' ':
        e.preventDefault()
        if (filteredOptions[highlightedIndex]) {
          onSelect(filteredOptions[highlightedIndex].value)
        }
        break
      case 'Escape':
        e.preventDefault()
        setOpen(false)
        break
    }
  }

  return (
    <div ref={containerRef} className="combobox-wrapper">
      <Button variant="outline" onClick={() => setOpen(!open)} className="combobox-trigger">
        {selected.length > 0 ? `${selected.length} tag${selected.length > 1 ? 's' : ''} selected` : placeholder}
        <Icon name="unfold_more" />
      </Button>

      {open && (
        <div className="combobox-dropdown">
          <div className="combobox-search">
            <input
              ref={inputRef}
              type="text"
              placeholder="Search tags..."
              value={searchQuery}
              onInput={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            {searchQuery && (
              <Icon
                name="close"
                className="clear-icon"
                onClick={() => setSearchQuery('')}
                onKeyDown={(e) => e.key === 'Enter' && setSearchQuery('')}
                role="button"
                tabIndex={0}
              />
            )}
          </div>

          <div ref={optionsRef} className="combobox-options">
            {filteredOptions.length === 0 ? (
              <div className="combobox-empty">No tags found.</div>
            ) : (
              filteredOptions.map((option, index) => {
                const isHighlighted = index === highlightedIndex
                return (
                  <div
                    key={option.value}
                    className={`combobox-option ${isHighlighted ? 'highlighted' : ''}`}
                    onClick={() => {
                      onSelect(option.value)
                    }}
                    onMouseEnter={() => setHighlightedIndex(index)}
                    role="option"
                    aria-selected={selected.includes(option.value)}
                  >
                    <Icon
                      name="check"
                      className={`check-icon ${selected.includes(option.value) ? '' : 'hidden'}`}
                    />
                    <span className={`tag-color-dot ${getTagColorClass(option.label)}`} />
                    {option.label}
                  </div>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
