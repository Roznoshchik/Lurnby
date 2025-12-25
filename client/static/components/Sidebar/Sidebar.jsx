import { useState } from 'preact/hooks';
import Button from '../Button/Button';
import Icon from '../Icon/Icon';
import logoCuteUrl from '../Logo/logo-cute.svg';
import './Sidebar.css';

export function Sidebar({ darkMode = false, onDarkModeToggle, showAppDashboard = false }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);

  const mainNavItems = [
    { href: '/client/articles', icon: 'book', label: 'Articles' },
    { href: '/client/highlights', icon: 'ink_highlighter', label: 'Highlights' },
    { href: '/client/review', icon: 'rotate_left', label: 'Review' },
    { href: '/client/tags', icon: 'sell', label: 'Tags' },
  ];

  if (showAppDashboard) {
    mainNavItems.push({ href: '/client/app_dashboard/users', icon: 'dashboard', label: 'Dashboard' });
  }

  const secondaryNavItems = [
    { href: 'https://www.patreon.com/lurnby', icon: 'favorite', label: 'Donate', external: true },
    { href: '/client/resources', icon: 'menu_book', label: 'Guides' },
    { href: '/client/settings', icon: 'settings', label: 'Settings' },
    { href: '/api/auth/logout', icon: 'logout', label: 'Logout' },
  ];

  return (
    <aside className={`sidebar ${isExpanded ? 'expanded' : 'collapsed'}`}>
      {/* Header */}
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <img src={logoCuteUrl} alt="Lurnby" className="icon" />
          {isExpanded && <span>Lurnby</span>}
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="sidebar-nav">
        <ul>
          {mainNavItems.map((item) => (
            <li key={item.href}>
              <a
                href={item.href}
                className={`nav-link ${!isExpanded ? 'centered' : ''}`}
                title={!isExpanded ? item.label : undefined}
              >
                <Icon name={item.icon} className="icon" />
                {isExpanded && <span>{item.label}</span>}
              </a>
            </li>
          ))}
        </ul>
      </nav>

      {/* Bottom Navigation */}
      <div className="sidebar-bottom">
        {/* Sidebar Toggle Button - Circular button at edge */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="sidebar-toggle-btn"
          aria-label={isExpanded ? "Collapse sidebar" : "Expand sidebar"}
        >
          <Icon name={isExpanded ? "chevron_left" : "chevron_right"} />
        </Button>

        {/* Dark Mode Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onDarkModeToggle}
          className={!isExpanded ? 'justify-center' : 'justify-start'}
          aria-label="Toggle dark mode"
        >
          <Icon name={darkMode ? "light_mode" : "dark_mode"} />
          {isExpanded && <span className="icon-label">{darkMode ? 'Light Mode' : 'Dark Mode'}</span>}
        </Button>

        {/* More Menu Button */}
        <div style={{ position: 'relative' }}>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setMenuOpen(!menuOpen)}
            className={!isExpanded ? 'justify-center' : 'justify-start'}
            aria-label="More options"
          >
            <Icon name="more_horiz" />
            {isExpanded && <span className="icon-label">More</span>}
          </Button>

          {/* Dropdown Menu */}
          {menuOpen && (
            <>
              {/* Backdrop to close menu */}
              <div
                className="menu-backdrop"
                onClick={() => setMenuOpen(false)}
              />

              {/* Menu Popover */}
              <div className={`menu-popover ${isExpanded ? 'expanded' : 'collapsed'}`}>
                <div className="menu-popover-content">
                  {secondaryNavItems.map((item) => (
                    <a
                      key={item.href}
                      href={item.href}
                      {...(item.external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
                      className="menu-link"
                      onClick={() => setMenuOpen(false)}
                    >
                      <Icon name={item.icon} className="icon" />
                      <span className="menu-link-label">
                        {item.label}
                        {item.external && <Icon name="open_in_new" className="external-icon" />}
                      </span>
                    </a>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </aside>
  );
}
