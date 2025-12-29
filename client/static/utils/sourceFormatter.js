/**
 * Converts article source URLs or filenames into readable, short display names
 * @param {string} source - The article source (URL, filename, or plain text)
 * @returns {string} A readable, shortened source name
 */
export function getReadableSource(source) {
  if (!source) return 'Unknown'

  const lowerSource = source.toLowerCase()

  // Handle "Epub File: added [date]" format
  if (lowerSource.startsWith('epub file:')) {
    return 'EPUB'
  }

  // Handle "PDF File: added [date]" format
  if (lowerSource.startsWith('pdf file:')) {
    return 'PDF'
  }

  // Handle "manually added [date]" format
  if (lowerSource.startsWith('manually added')) {
    return 'Manual'
  }

  // Handle EPUB files by extension
  if (lowerSource.includes('.epub')) {
    return 'EPUB'
  }

  // Handle PDF files by extension
  if (lowerSource.includes('.pdf')) {
    return 'PDF'
  }

  // If it's already a clean name (no URL pattern), return it (truncated if needed)
  if (!source.includes('://') && !source.includes('.')) {
    return source.length > 20 ? `${source.slice(0, 20)}...` : source
  }

  try {
    // Try to parse as URL
    const url = new URL(source.startsWith('http') ? source : `https://${source}`)
    let domain = url.hostname

    // If hostname is empty or just dots, fall back to original source
    if (!domain || domain.trim() === '' || /^\.+$/.test(domain)) {
      return source.length > 20 ? `${source.slice(0, 20)}...` : source
    }

    // Remove www. prefix
    domain = domain.replace(/^www\./, '')

    // Remove common TLDs and get the main domain name
    const parts = domain.split('.')
    const mainDomain = parts[0]

    // If main domain is empty, fall back to original source
    if (!mainDomain || mainDomain.trim() === '') {
      return source.length > 20 ? `${source.slice(0, 20)}...` : source
    }

    // Capitalize first letter
    const result = mainDomain.charAt(0).toUpperCase() + mainDomain.slice(1)

    // Truncate if too long
    return result.length > 20 ? `${result.slice(0, 20)}...` : result
  } catch {
    // If URL parsing fails, just return the original (truncated if needed)
    return source.length > 20 ? `${source.slice(0, 20)}...` : source
  }
}
