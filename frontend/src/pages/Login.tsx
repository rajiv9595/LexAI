import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate, Navigate } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import Button from '../components/Button'
import DisclaimerBanner from '../components/DisclaimerBanner'
import { useAuth } from '../hooks/useAuth'
import { ApiError } from '../services/apiClient'
import './pages.css'

function Login() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Redirect if already logged in
  if (isAuthenticated) {
    return <Navigate to="/app/dashboard" replace />
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)

    const trimmedEmail = email.trim()
    if (!trimmedEmail) {
      setError('Please enter your email address.')
      return
    }

    if (!password) {
      setError('Please enter your password.')
      return
    }

    setIsSubmitting(true)

    try {
      await login({
        email: trimmedEmail,
        password,
      })
      const from = (location.state as { from?: { pathname?: string } })?.from
        ?.pathname
      navigate(from || '/app/dashboard', { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          setError('Invalid email or password. Please try again.')
        } else {
          setError(err.detail || 'An error occurred during login. Please try again.')
        }
      } else if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('An unexpected error occurred. Please try again.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="page-container">
      <PageHeader
        title="Log in"
        description="Access your LexAssist workspace."
      />
      <div className="placeholder-stack">
        <Card title="Welcome back" description="Sign in to your account.">
          {error ? (
            <div
              className="auth-error-alert"
              role="alert"
              aria-live="polite"
            >
              {error}
            </div>
          ) : null}
          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <div className="auth-form-field">
              <label htmlFor="login-email">Email</label>
              <input
                id="login-email"
                name="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                disabled={isSubmitting}
              />
            </div>
            <div className="auth-form-field">
              <label htmlFor="login-password">Password</label>
              <input
                id="login-password"
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                disabled={isSubmitting}
              />
            </div>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Logging in...' : 'Log in'}
            </Button>
          </form>
          <p className="auth-switch">
            Need an account? <Link to="/register">Create an account</Link>
          </p>
        </Card>
        <DisclaimerBanner />
      </div>
    </div>
  )
}

export default Login
