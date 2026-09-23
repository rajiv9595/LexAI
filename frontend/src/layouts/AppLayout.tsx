import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Header from '../components/Header'
import Sidebar from '../components/Sidebar'
import './layouts.css'

const titles: Record<string, string> = {
  '/app/dashboard': 'Dashboard',
  '/app/assistant': 'Legal Assistant',
  '/app/documents': 'Document Assistant',
  '/app/documents/create': 'Create Document',
  '/app/research': 'Legal Research',
  '/app/history': 'Case History',
  '/app/profile': 'Profile',
  '/app/settings': 'Settings',
}

function getTitle(pathname: string): string {
  if (titles[pathname]) {
    return titles[pathname]
  }
  if (pathname.startsWith('/app/documents/')) {
    return 'Document Details'
  }
  return 'LexAssist'
}

function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="app-shell">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="app-main-column">
        <Header
          title={getTitle(location.pathname)}
          onMenuClick={() => setSidebarOpen((value) => !value)}
        />
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default AppLayout
