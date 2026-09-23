import type { ReactNode } from 'react'
import './layouts.css'

interface AuthLayoutProps {
  children: ReactNode
}

function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="auth-layout">
      <div className="auth-card">
        <div className="auth-brand">
          <p className="auth-brand-name">LexAssist</p>
          <p className="auth-brand-tagline">
            Intelligent Legal Assistance, Simplified.
          </p>
        </div>
        {children}
      </div>
    </div>
  )
}

export default AuthLayout
