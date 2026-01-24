import { useRef, useCallback } from 'preact/hooks'
import QuillEditor from '../QuillEditor/QuillEditor'
import Button from '../Button/Button'
import Icon from '../Icon/Icon'
import './NotesPanel.css'

export function NotesPanel({ notes, onChange, onClose }) {
  const quillRef = useRef(null)
  const saveTimeoutRef = useRef(null)

  const handleTextChange = useCallback(() => {
    if (!quillRef.current) return

    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }

    saveTimeoutRef.current = setTimeout(() => {
      const html = quillRef.current.root.innerHTML
      onChange(html)
    }, 1000)
  }, [onChange])

  return (
    <div className="notes-panel">
      <div className="notes-panel-header">
        <h3>Notes</h3>
        <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close notes">
          <Icon name="close" />
        </Button>
      </div>
      <div className="notes-panel-editor">
        <QuillEditor
          ref={quillRef}
          defaultValue={notes}
          onTextChange={handleTextChange}
          placeholder="Write your notes here..."
        />
      </div>
    </div>
  )
}
