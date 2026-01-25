import { useEffect, useRef, useState, useCallback } from 'preact/hooks'
import { createPortal } from 'preact/compat'
import './Popover.css'

/**
 * Generic Popover component that positions itself relative to an anchor rect,
 * constrained within a container.
 *
 * @param {boolean} isOpen - Controls visibility
 * @param {function} onClose - Called when popover should close
 * @param {DOMRect|{top,left,width,height,right,bottom}} anchorRect - Position to anchor to
 * @param {RefObject} containerRef - Container to constrain popover within
 * @param {string} placement - Where to place: top, top-start, top-end, bottom, bottom-start, bottom-end, left, right
 * @param {number} offset - Gap between anchor and popover (default: 8)
 * @param {string} className - Additional CSS classes
 * @param {preact.ComponentChildren} children - Popover content
 */
export default function Popover({
  isOpen,
  onClose,
  anchorRect,
  containerRef,
  placement = 'top',
  offset = 8,
  className = '',
  children,
}) {
  const popoverRef = useRef(null)
  const [position, setPosition] = useState({ top: 0, left: 0 })

  const calculatePosition = useCallback(() => {
    if (!anchorRect || !popoverRef.current) return

    const popover = popoverRef.current
    const popoverRect = popover.getBoundingClientRect()

    // Get container bounds (fall back to viewport if no container)
    const container = containerRef?.current
    const bounds = container
      ? container.getBoundingClientRect()
      : { top: 0, left: 0, right: window.innerWidth, bottom: window.innerHeight }

    const padding = 8
    let top = 0
    let left = 0

    // Calculate base position based on placement
    switch (placement) {
      case 'top':
        top = anchorRect.top - popoverRect.height - offset
        left = anchorRect.left + anchorRect.width / 2 - popoverRect.width / 2
        break
      case 'top-start':
        top = anchorRect.top - popoverRect.height - offset
        left = anchorRect.left
        break
      case 'top-end':
        top = anchorRect.top - popoverRect.height - offset
        left = anchorRect.right - popoverRect.width
        break
      case 'bottom':
        top = anchorRect.bottom + offset
        left = anchorRect.left + anchorRect.width / 2 - popoverRect.width / 2
        break
      case 'bottom-start':
        top = anchorRect.bottom + offset
        left = anchorRect.left
        break
      case 'bottom-end':
        top = anchorRect.bottom + offset
        left = anchorRect.right - popoverRect.width
        break
      case 'left':
        top = anchorRect.top + anchorRect.height / 2 - popoverRect.height / 2
        left = anchorRect.left - popoverRect.width - offset
        break
      case 'right':
        top = anchorRect.top + anchorRect.height / 2 - popoverRect.height / 2
        left = anchorRect.right + offset
        break
      default:
        top = anchorRect.top - popoverRect.height - offset
        left = anchorRect.left + anchorRect.width / 2 - popoverRect.width / 2
    }

    // Constrain within container bounds
    if (left < bounds.left + padding) {
      left = bounds.left + padding
    }
    if (left + popoverRect.width > bounds.right - padding) {
      left = bounds.right - popoverRect.width - padding
    }

    // Flip vertically if needed
    if (top < bounds.top + padding && placement.startsWith('top')) {
      // Flip to bottom
      top = anchorRect.bottom + offset
    } else if (top < bounds.top + padding) {
      top = bounds.top + padding
    }

    if (top + popoverRect.height > bounds.bottom - padding && placement.startsWith('bottom')) {
      // Flip to top
      top = anchorRect.top - popoverRect.height - offset
    } else if (top + popoverRect.height > bounds.bottom - padding) {
      top = bounds.bottom - popoverRect.height - padding
    }

    setPosition({ top, left })
  }, [anchorRect, containerRef, placement, offset])

  // Calculate position after render
  useEffect(() => {
    if (isOpen && anchorRect) {
      requestAnimationFrame(calculatePosition)
    }
  }, [isOpen, anchorRect, calculatePosition])

  // Handle click outside
  useEffect(() => {
    if (!isOpen) return

    const handleClickOutside = (e) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target)) {
        onClose()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen, onClose])

  // Handle Escape key
  useEffect(() => {
    if (!isOpen) return

    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose()
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  if (!isOpen || !anchorRect) return null

  const popover = (
    <div
      ref={popoverRef}
      className={`popover ${className}`}
      style={{ top: `${position.top}px`, left: `${position.left}px` }}
      role="dialog"
    >
      {children}
    </div>
  )

  return createPortal(popover, document.body)
}
