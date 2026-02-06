# Reusable Components

This document lists the reusable components available in the client codebase.

## UI Components

### Icon
Material Symbols icon wrapper.

```jsx
import Icon from './components/Icon/Icon'

<Icon name="check_circle" />
<Icon name="edit" filled />
<Icon name="menu" className="custom-class" />
```

**Props:**
- `name` (required): Material Symbols icon name
- `variant`: 'outlined' (default) | 'rounded' | 'sharp'
- `filled`: boolean - use filled variant
- `className`: additional CSS classes
- `...props`: additional props passed through (onClick, etc.)

### Button
Styled button with variants.

```jsx
import Button from './components/Button/Button'

<Button variant="default">Primary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="destructive">Delete</Button>
<Button size="sm" icon="add">Small with icon</Button>
```

**Props:**
- `variant`: 'default' | 'outline' | 'ghost' | 'destructive'
- `size`: 'sm' | 'md' | 'lg'
- `icon`: icon name to prepend
- `disabled`: boolean
- `className`: additional CSS classes

### Badge
Small label/tag component.

```jsx
import Badge from './components/Badge/Badge'

<Badge>Default</Badge>
<Badge variant="outline">Outline</Badge>
```

### Progress
Progress bar component.

```jsx
import Progress from './components/Progress/Progress'

<Progress value={75} />
<Progress value={50} className="custom" />
```

**Props:**
- `value`: 0-100 percentage
- `className`: additional CSS classes

### Loader
Loading indicator with three display modes.

```jsx
import Loader from './components/Loader/Loader'

// Card mode (default): replaces children when loading
<Loader isLoading={loading} text="Loading...">
  <Content />
</Loader>

// Inline mode: small spinner for buttons
<Button>
  Save
  <Loader isLoading={saving} mode="inline" />
</Button>

// Overlay mode: covers children with semi-transparent overlay
<Loader isLoading={submitting} mode="overlay" text="Submitting...">
  <Form />
</Loader>
```

**Props:**
- `isLoading`: boolean - whether to show the loader
- `mode`: 'card' (default) | 'inline' | 'overlay'
- `text`: optional text to display with spinner
- `className`: additional CSS classes
- `children`: content to wrap (not used for inline mode)

### Card
Base card component with variants and padding options.

```jsx
import Card from './components/Card/Card'

<Card>Default card</Card>
<Card variant="outline">Outline card</Card>
<Card padding="lg">Large padding</Card>
<Card as="button" interactive onClick={handleClick}>Clickable card</Card>
<Card as="article" className="article-card">Semantic card</Card>
```

**Props:**
- `variant`: 'default' | 'outline'
- `padding`: 'sm' | 'md' | 'lg' | 'xl'
- `interactive`: boolean - adds hover effects and cursor pointer
- `as`: HTML element or component to render as ('div', 'button', 'article', etc.)
- `onClick`: click handler (useful with interactive)
- `className`: additional CSS classes

### Modal
Reusable modal dialog with overlay, header, body, and footer.

```jsx
import Modal from './components/Modal/Modal'

<Modal
  isOpen={showModal}
  onClose={() => setShowModal(false)}
  title="Modal Title"
  size="lg"
  footer={<Button onClick={save}>Save</Button>}
>
  <p>Modal content goes here</p>
</Modal>
```

**Props:**
- `isOpen`: boolean - controls visibility
- `onClose`: callback when modal should close
- `title`: modal header title
- `size`: 'sm' | 'md' | 'lg' | 'xl'
- `footer`: JSX for footer actions
- `className`: additional CSS classes

### Popover
Positioned popover anchored to a rect, constrained within a container.

```jsx
import Popover from './components/Popover/Popover'

// Get selection rect
const rect = window.getSelection().getRangeAt(0).getBoundingClientRect()

<Popover
  isOpen={showPopover}
  onClose={() => setShowPopover(false)}
  anchorRect={rect}
  containerRef={readerContentRef}
  placement="top"
>
  <div className="popover-toolbar">
    <button onClick={handleAction}>Action</button>
  </div>
</Popover>
```

**Props:**
- `isOpen`: boolean - controls visibility
- `onClose`: callback when popover should close
- `anchorRect`: DOMRect or `{top, left, width, height, right, bottom}` to position relative to
- `containerRef`: ref to container element (popover stays within bounds)
- `placement`: 'top' | 'top-start' | 'top-end' | 'bottom' | 'bottom-start' | 'bottom-end' | 'left' | 'right'
- `offset`: gap between anchor and popover (default: 8)
- `className`: additional CSS classes

**CSS classes for content:**
- `.popover-toolbar`: horizontal button row
- `.popover-content`: padded content wrapper
- `.popover-divider`: vertical divider between button groups

## Layout Components

### Layout
Main app layout with sidebar/mobile nav.

```jsx
import { Layout } from './components/Layout/Layout'

<Layout>
  {/* Page content */}
</Layout>
```

### Sidebar
Desktop navigation sidebar (used internally by Layout).

### MobileNav
Mobile bottom navigation (used internally by Layout).

## Auth Components

### RequireAuth
Wrapper that redirects unauthenticated users to login.

```jsx
import RequireAuth from './components/RequireAuth/RequireAuth'

<RequireAuth>
  <ProtectedContent />
</RequireAuth>
```

### ErrorBoundary
Catches React errors and displays fallback UI.

```jsx
import ErrorBoundary from './components/ErrorBoundary/ErrorBoundary'

<ErrorBoundary>
  <ComponentThatMightError />
</ErrorBoundary>
```

## Form Components

### Select
Styled dropdown select wrapper.

```jsx
import Select from './components/Select/Select'

<Select
  options={[{ value: 'a', label: 'Option A' }]}
  value={selected}
  onChange={setSelected}
  placeholder="Choose..."
/>
```

### Combobox
Multi-select dropdown with search and optional inline creation.

```jsx
import Combobox from './components/Combobox/Combobox'

<Combobox
  options={[{ value: 'tag1', label: 'Tag 1' }]}
  selected={selectedTags}
  onSelect={toggleTag}
  placeholder="Select tags..."
  onCreate={(name) => createTag(name)}
/>
```

**Props:**
- `options`: array of `{ value, label }` objects
- `selected`: array of selected values
- `onSelect`: callback when option is selected/deselected
- `placeholder`: placeholder text
- `onCreate`: callback to create new item (shows "Create [query]" option when provided)

### QuillEditor
Rich text editor using Quill.js. Uncontrolled component with ref for accessing Quill instance.

```jsx
import { useRef } from 'preact/hooks'
import QuillEditor from './components/QuillEditor/QuillEditor'

const editorRef = useRef(null)

<QuillEditor
  ref={editorRef}
  defaultValue="<p>Initial content</p>"
  placeholder="Start typing..."
  onTextChange={(delta, oldDelta, source) => console.log('Changed')}
/>

// Access content: editorRef.current?.root.innerHTML
```

**Props:**
- `defaultValue`: initial HTML content
- `placeholder`: placeholder text
- `readOnly`: boolean
- `modules`: Quill modules config (toolbar, etc.)
- `boundsRef`: ref to container element for tooltip positioning (prevents clipping in modals)
- `onTextChange`: callback on content change
- `onSelectionChange`: callback on selection change
- `className`: additional CSS classes
