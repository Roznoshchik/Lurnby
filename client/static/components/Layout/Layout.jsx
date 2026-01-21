import { useEffect, useState } from 'preact/hooks'
import { Toaster } from 'sonner'
import { MobileNav } from '../MobileNav/MobileNav'
import { Sidebar } from '../Sidebar/Sidebar'
import './Layout.css'

export function Layout({ children, showAppDashboard = false, sidebarContent = null }) {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode')
    return saved === 'true'
  })
  const [sidebarExpanded, setSidebarExpanded] = useState(false)

  // Apply dark mode class to document root and persist
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('darkMode', darkMode)
  }, [darkMode])

  return (
    <div className="app-container">
      <Toaster
        position="top-right"
        swipeDirections={['left', 'right']}
        toastOptions={{
          unstyled: true,
          classNames: {
            toast: 'toast',
            title: 'toast-title',
            description: 'toast-description',
            success: 'toast-success',
            error: 'toast-error',
            warning: 'toast-warning',
            info: 'toast-info',
            actionButton: 'toast-action',
            cancelButton: 'toast-cancel',
            closeButton: 'toast-close',
          },
        }}
      />

      <Sidebar
        darkMode={darkMode}
        onDarkModeToggle={() => setDarkMode(!darkMode)}
        showAppDashboard={showAppDashboard}
        isExpanded={sidebarExpanded}
        onToggle={() => setSidebarExpanded(!sidebarExpanded)}
        sidebarContent={sidebarContent}
      />

      <MobileNav
        darkMode={darkMode}
        onDarkModeToggle={() => setDarkMode(!darkMode)}
        showAppDashboard={showAppDashboard}
      />

      <div className={`main-content ${sidebarExpanded ? 'sidebar-expanded' : 'sidebar-collapsed'}`}>
        {children}
      </div>
    </div>
  )
}
