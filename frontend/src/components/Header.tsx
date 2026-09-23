import { useAuth } from '../hooks/useAuth'
import './Header.css'

interface HeaderProps {
  title: string
  onMenuClick: () => void
}

function Header({ title, onMenuClick }: HeaderProps) {
  const { user, logout } = useAuth()

  const displayName = user?.display_name || 'LexAssist User'
  const emailOrRole = user?.email || 'Authenticated User'
  const initial = (user?.display_name?.trim()?.[0] || 'U').toUpperCase()

  return (
    <header className="app-header">
      <div className="app-header-left">
        <button
          type="button"
          className="menu-button"
          onClick={onMenuClick}
          aria-label="Toggle navigation menu"
        >
          Menu
        </button>
        <h1 className="app-header-title">{title}</h1>
      </div>
      <div className="app-header-right">
        <button
          type="button"
          className="notification-button"
          aria-label="Notifications"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 18 18"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            focusable="false"
          >
            <path d="M9 2a5 5 0 0 0-5 5v3L2.5 12.5h13L14 10V7a5 5 0 0 0-5-5z" />
            <path d="M7 15a2 2 0 0 0 4 0" />
          </svg>
          <span className="notification-label">Notifications</span>
        </button>
        <div className="user-block">
          <span className="user-avatar" aria-hidden="true">
            {initial}
          </span>
          <span className="user-meta">
            <span className="user-name">{displayName}</span>
            <span className="user-role">{emailOrRole}</span>
          </span>
        </div>
        <button
          type="button"
          className="logout-button"
          onClick={logout}
          aria-label="Log out"
        >
          Log out
        </button>
      </div>
    </header>
  )
}

export default Header
