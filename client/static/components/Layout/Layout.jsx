import { useState } from 'preact/hooks';
import { Sidebar } from '../Sidebar/Sidebar';
import { MobileNav } from '../MobileNav/MobileNav';
import './Layout.css';

export function Layout({ children, showAppDashboard = false }) {
  const [darkMode, setDarkMode] = useState(false);

  return (
    <div className="app-container">
      <Sidebar
        darkMode={darkMode}
        onDarkModeToggle={() => setDarkMode(!darkMode)}
        showAppDashboard={showAppDashboard}
      />

      <MobileNav
        darkMode={darkMode}
        onDarkModeToggle={() => setDarkMode(!darkMode)}
        showAppDashboard={showAppDashboard}
      />

      <div className="main-content">
        {children}
      </div>
    </div>
  );
}
