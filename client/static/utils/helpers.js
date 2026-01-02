// Total number of tag colors defined in CSS
const TAG_COLOR_COUNT = 9

/**
 * Generates a consistent hash from a string.
 */
function hashString(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = (hash << 5) - hash + char
    hash = hash & hash
  }
  return Math.abs(hash)
}

/**
 * Returns a consistent CSS class for a tag based on its name.
 */
export function getTagColorClass(tagName) {
  const hash = hashString(tagName.toLowerCase())
  const colorIndex = hash % TAG_COLOR_COUNT
  return `tag-color-${colorIndex}`
}
