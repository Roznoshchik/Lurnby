import Popover from '../Popover/Popover'
import Icon from '../Icon/Icon'
import './HighlightPopover.css'

/**
 * Popover that appears on text selection to create highlights.
 *
 * @param {boolean} isOpen - Controls visibility
 * @param {function} onClose - Called when popover should close
 * @param {DOMRect} anchorRect - Selection rect to anchor to
 * @param {RefObject} containerRef - Container to constrain popover within
 * @param {function} onHighlight - Called for quick highlight (no modal)
 * @param {function} onHighlightWithNotes - Called to open highlight modal
 */
export default function HighlightPopover({
  isOpen,
  onClose,
  anchorRect,
  containerRef,
  onHighlight,
  onHighlightWithNotes,
}) {
  const handleHighlight = () => {
    onHighlight?.()
    onClose()
  }

  const handleHighlightWithNotes = () => {
    onHighlightWithNotes?.()
    onClose()
  }

  return (
    <Popover
      isOpen={isOpen}
      onClose={onClose}
      anchorRect={anchorRect}
      containerRef={containerRef}
      placement="top"
      className="highlight-popover"
    >
      <div className="popover-toolbar">
        <button
          type="button"
          onClick={handleHighlight}
          title="Quick highlight"
          aria-label="Create highlight"
        >
          <Icon name="ink_highlighter" />
        </button>
        <button
          type="button"
          onClick={handleHighlightWithNotes}
          title="Highlight with notes"
          aria-label="Create highlight with notes"
        >
          <Icon name="note_add" />
        </button>
      </div>
    </Popover>
  )
}
