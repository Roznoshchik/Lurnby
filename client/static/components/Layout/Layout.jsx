import { useState, useEffect } from 'preact/hooks';
import { Sidebar } from '../Sidebar/Sidebar';
import { MobileNav } from '../MobileNav/MobileNav';
import './Layout.css';

export function Layout({ children, showAppDashboard = false }) {
  const [darkMode, setDarkMode] = useState(false);
  const [sidebarExpanded, setSidebarExpanded] = useState(false);

  // Apply dark mode class to document root
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  return (
    <div className="app-container">
      <Sidebar
        darkMode={darkMode}
        onDarkModeToggle={() => setDarkMode(!darkMode)}
        showAppDashboard={showAppDashboard}
        isExpanded={sidebarExpanded}
        onToggle={() => setSidebarExpanded(!sidebarExpanded)}
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
  );
}
