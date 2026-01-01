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

## Content Components

### ArticleCard
Full article card for articles grid.

```jsx
import ArticleCard from './components/ArticleCard/ArticleCard'

<ArticleCard
  article={articleObj}
  onOpen={() => openArticle(article)}
  onEdit={() => editArticle(article)}
/>
```

### ArticlePreview
Compact article card for "Recently Opened" section.

```jsx
import ArticlePreview from './components/ArticlePreview/ArticlePreview'

<ArticlePreview
  article={articleObj}
  onOpen={() => openArticle(article)}
  onEdit={() => editArticle(article)}
/>
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
Multi-select dropdown with search.

```jsx
import Combobox from './components/Combobox/Combobox'

<Combobox
  options={[{ value: 'tag1', label: 'Tag 1' }]}
  selected={selectedTags}
  onSelect={toggleTag}
  placeholder="Select tags..."
/>
```
