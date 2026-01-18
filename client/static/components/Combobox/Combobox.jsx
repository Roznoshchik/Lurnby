import { useState, useRef, useEffect, useMemo } from 'preact/hooks'
import Button from '../Button/Button'
import Icon from '../Icon/Icon'
import { getTagColorClass } from '../../utils/helpers'
import './Combobox.css'

export default function Combobox({
  options,
  selected,
  onSelect,
  placeholder = 'Select...',
  onCreate,
}) {
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
    return options.filter((option) =>
      option.label.toLowerCase().includes(searchQuery.toLowerCase()),
    )
  }, [options, searchQuery])

  // Show "Create" option when onCreate is provided and no exact match exists
  const trimmedQuery = searchQuery.trim()
  const showCreateOption =
    onCreate &&
    trimmedQuery &&
    !options.some((opt) => opt.label.toLowerCase() === trimmedQuery.toLowerCase())

  // Total navigable items (filtered options + create option if shown)
  const totalItems = filteredOptions.length + (showCreateOption ? 1 : 0)

  const handleKeyDown = (e) => {
    if (!open) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex((prev) => (prev < totalItems - 1 ? prev + 1 : 0))
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : totalItems - 1))
        break
      case 'Enter':
        e.preventDefault()
        // Create option is at the end (index = filteredOptions.length)
        if (showCreateOption && highlightedIndex === filteredOptions.length) {
          handleCreate()
        } else if (filteredOptions[highlightedIndex]) {
          onSelect(filteredOptions[highlightedIndex].value)
        }
        break
      case 'Escape':
        e.preventDefault()
        e.stopPropagation()
        setOpen(false)
        break
    }
  }

  const handleCreate = () => {
    if (onCreate && searchQuery.trim()) {
      onCreate(searchQuery.trim())
      setSearchQuery('')
    }
  }

  return (
    <div ref={containerRef} className="combobox-wrapper">
      <Button variant="outline" onClick={() => setOpen(!open)} className="combobox-trigger">
        {selected.length > 0
          ? `${selected.length} tag${selected.length > 1 ? 's' : ''} selected`
          : placeholder}
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
                onClick={(e) => {
                  e.stopPropagation()
                  setSearchQuery('')
                }}
                onKeyDown={(e) => e.key === 'Enter' && setSearchQuery('')}
                role="button"
                tabIndex={0}
              />
            )}
          </div>

          <div ref={optionsRef} className="combobox-options">
            {filteredOptions.length === 0 && !showCreateOption ? (
              <div className="combobox-empty">No tags found.</div>
            ) : (
              <>
                {filteredOptions.map((option, index) => {
                  const isHighlighted = index === highlightedIndex
                  return (
                    <div
                      key={option.value}
                      className={`combobox-option ${isHighlighted ? 'highlighted' : ''}`}
                      onClick={() => {
                        onSelect(option.value)
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault()
                          onSelect(option.value)
                        }
                      }}
                      onMouseEnter={() => setHighlightedIndex(index)}
                      role="option"
                      tabIndex={0}
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
                })}
                {showCreateOption && (
                  <div
                    className={`combobox-option combobox-create-option ${highlightedIndex === filteredOptions.length ? 'highlighted' : ''}`}
                    onClick={handleCreate}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        handleCreate()
                      }
                    }}
                    onMouseEnter={() => setHighlightedIndex(filteredOptions.length)}
                    role="option"
                    tabIndex={0}
                  >
                    <Icon name="add" className="create-icon" />
                    Create "{searchQuery.trim()}"
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
