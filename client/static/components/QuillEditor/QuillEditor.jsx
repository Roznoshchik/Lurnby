import { useRef, useEffect, useLayoutEffect } from 'preact/hooks'
import { forwardRef } from 'preact/compat'
import Quill from 'quill'
import 'quill/dist/quill.snow.css'
import './QuillEditor.css'

const DEFAULT_MODULES = {
  toolbar: [
    ['bold', 'italic', 'underline', 'strike'],
    ['blockquote', 'code-block'],
    [{ list: 'ordered' }, { list: 'bullet' }],
    ['link'],
    ['clean'],
  ],
}

const QuillEditor = forwardRef(
  (
    {
      defaultValue = '',
      onTextChange,
      onSelectionChange,
      readOnly = false,
      placeholder = '',
      modules = DEFAULT_MODULES,
      boundsRef = null,
      className = '',
    },
    ref,
  ) => {
    const containerRef = useRef(null)
    const defaultValueRef = useRef(defaultValue)
    const onTextChangeRef = useRef(onTextChange)
    const onSelectionChangeRef = useRef(onSelectionChange)

    useLayoutEffect(() => {
      onTextChangeRef.current = onTextChange
      onSelectionChangeRef.current = onSelectionChange
    })

    useEffect(() => {
      if (ref?.current) {
        ref.current.enable(!readOnly)
      }
    }, [ref, readOnly])

    useEffect(() => {
      const container = containerRef.current
      const editorContainer = container.appendChild(container.ownerDocument.createElement('div'))

      // Use the bounds element if provided, otherwise default to the container itself
      const boundsElement = boundsRef?.current || container

      const quill = new Quill(editorContainer, {
        theme: 'snow',
        placeholder,
        modules,
        bounds: boundsElement,
      })

      if (ref) {
        ref.current = quill
      }

      if (defaultValueRef.current) {
        quill.root.innerHTML = defaultValueRef.current
      }

      quill.on(Quill.events.TEXT_CHANGE, (...args) => {
        onTextChangeRef.current?.(...args)
      })

      quill.on(Quill.events.SELECTION_CHANGE, (...args) => {
        onSelectionChangeRef.current?.(...args)
      })

      return () => {
        if (ref) {
          ref.current = null
        }
        container.innerHTML = ''
      }
    }, [ref])

    return <div ref={containerRef} className={`quill-editor ${className}`} />
  },
)

QuillEditor.displayName = 'QuillEditor'

export default QuillEditor
