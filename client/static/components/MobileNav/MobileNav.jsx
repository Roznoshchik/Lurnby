import { useState } from 'preact/hooks';
import Button from '../Button/Button';
import Icon from '../Icon/Icon';
import logoCuteUrl from '../Logo/logo-cute.svg';
import './MobileNav.css';

export function MobileNav({ darkMode = false, onDarkModeToggle, showAppDashboard = false }) {
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
    <>
      {/* Mobile Top Header */}
      <header className="mobile-header">
        <div className="mobile-header-content">
          <div className="mobile-logo">
            <img src={logoCuteUrl} alt="Lurnby" className="icon" />
            <span>Lurnby</span>
          </div>

          <div className="mobile-header-actions">
            <Button
              variant="ghost"
              size="sm"
              onClick={onDarkModeToggle}
              aria-label="Toggle dark mode"
            >
              <Icon name={darkMode ? "light_mode" : "dark_mode"} />
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label="Toggle menu"
            >
              <Icon name="more_horiz" />
            </Button>
          </div>
        </div>

        {/* Mobile Dropdown Menu (for secondary items) */}
        {menuOpen && (
          <div className="mobile-dropdown">
            <nav>
              <ul>
                {secondaryNavItems.map((item) => (
                  <li key={item.href}>
                    <a
                      href={item.href}
                      {...(item.external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
                      className="nav-link"
                      onClick={() => setMenuOpen(false)}
                    >
                      <Icon name={item.icon} className="icon" />
                      <span className="menu-link-label">
                        {item.label}
                        {item.external && <Icon name="open_in_new" className="external-icon" />}
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          </div>
        )}
      </header>

      {/* Mobile Bottom Tab Bar */}
      <nav className="mobile-tab-bar">
        <div className="mobile-tab-bar-content">
          {mainNavItems.slice(0, 4).map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="tab-link"
            >
              <Icon name={item.icon} className="icon" />
              <span>{item.label}</span>
            </a>
          ))}
        </div>
      </nav>
    </>
  );
}
