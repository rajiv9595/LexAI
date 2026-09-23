import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import './Sidebar.css'

interface SidebarProps {
  open: boolean
  onClose: () => void
}

interface NavItem {
  to: string
  label: string
  end?: boolean
  icon: ReactNode
}

interface NavSection {
  title: string
  items: NavItem[]
}

function NavIcon({ children }: { children: ReactNode }) {
  return (
    <svg
      className="sidebar-link-icon"
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  )
}

const sections: NavSection[] = [
  {
    title: 'Overview',
    items: [
      {
        to: '/app/dashboard',
        label: 'Dashboard',
        end: true,
        icon: (
          <NavIcon>
            <rect x="1.5" y="1.5" width="5" height="5" rx="1" />
            <rect x="9.5" y="1.5" width="5" height="5" rx="1" />
            <rect x="1.5" y="9.5" width="5" height="5" rx="1" />
            <rect x="9.5" y="9.5" width="5" height="5" rx="1" />
          </NavIcon>
        ),
      },
    ],
  },
  {
    title: 'Legal Assistance',
    items: [
      {
        to: '/app/assistant',
        label: 'Legal Assistant',
        icon: (
          <NavIcon>
            <path d="M2 3.5h12v7H8l-3.5 3v-3H2v-7z" />
            <path d="M5 6.5h6M5 8.5h4" />
          </NavIcon>
        ),
      },
      {
        to: '/app/documents',
        label: 'Documents',
        icon: (
          <NavIcon>
            <path d="M4 1.5h5.5L12.5 4.5v10H4v-13z" />
            <path d="M9.5 1.5v3h3" />
            <path d="M6 8h4M6 10.5h4" />
          </NavIcon>
        ),
      },
      {
        to: '/app/research',
        label: 'Legal Research',
        icon: (
          <NavIcon>
            <circle cx="7" cy="7" r="4.5" />
            <path d="M10.5 10.5L14.5 14.5" />
          </NavIcon>
        ),
      },
    ],
  },
  {
    title: 'Workspace',
    items: [
      {
        to: '/app/history',
        label: 'Case History',
        icon: (
          <NavIcon>
            <circle cx="8" cy="8" r="6.5" />
            <path d="M8 4.5V8l2.5 1.5" />
          </NavIcon>
        ),
      },
    ],
  },
  {
    title: 'Account',
    items: [
      {
        to: '/app/profile',
        label: 'Profile',
        icon: (
          <NavIcon>
            <circle cx="8" cy="5.5" r="2.5" />
            <path d="M2.5 14.5c0-3 2.5-4.5 5.5-4.5s5.5 1.5 5.5 4.5" />
          </NavIcon>
        ),
      },
      {
        to: '/app/settings',
        label: 'Settings',
        icon: (
          <NavIcon>
            <circle cx="8" cy="8" r="2" />
            <path d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2M3.4 3.4l1.4 1.4M11.2 11.2l1.4 1.4M12.6 3.4l-1.4 1.4M4.8 11.2l-1.4 1.4" />
          </NavIcon>
        ),
      },
    ],
  },
]

function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {open ? (
        <button
          type="button"
          className="sidebar-overlay"
          aria-label="Close navigation menu"
          onClick={onClose}
        />
      ) : null}
      <aside className={`sidebar${open ? ' open' : ''}`}>
        <div className="sidebar-brand">
          <div className="sidebar-brand-row">
            <span className="sidebar-brand-mark" aria-hidden="true">
              §
            </span>
            <div>
              <p className="sidebar-brand-name">LexAssist</p>
              <p className="sidebar-brand-tagline">Legal Assistance Platform</p>
            </div>
          </div>
          <button
            type="button"
            className="sidebar-close-button"
            onClick={onClose}
            aria-label="Close navigation menu"
          >
            Close
          </button>
        </div>
        <nav className="sidebar-nav" aria-label="Primary">
          {sections.map((section) => (
            <div key={section.title} className="sidebar-section">
              <p className="sidebar-section-title">{section.title}</p>
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  onClick={onClose}
                  aria-label={item.label}
                  className={({ isActive }) =>
                    isActive ? 'sidebar-link active' : 'sidebar-link'
                  }
                >
                  {item.icon}
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <p className="sidebar-footer-title">AI-assisted legal information</p>
          <p className="sidebar-footer-text">
            Review important matters with a qualified legal professional.
          </p>
        </div>
      </aside>
    </>
  )
}

export default Sidebar
