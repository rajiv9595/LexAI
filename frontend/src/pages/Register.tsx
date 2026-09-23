import { useState, type FormEvent } from 'react'
import { Link, useNavigate, Navigate } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import Button from '../components/Button'
import DisclaimerBanner from '../components/DisclaimerBanner'
import { useAuth } from '../hooks/useAuth'
import { ApiError } from '../services/apiClient'
import './pages.css'

function Register() {
  const { register, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Redirect if already logged in
  if (isAuthenticated) {
    return <Navigate to="/app/dashboard" replace />
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)

    const trimmedName = displayName.trim()
    if (!trimmedName) {
      setError('Please enter your full display name.')
      return
    }

    const trimmedEmail = email.trim()
    if (!trimmedEmail) {
      setError('Please enter your email address.')
      return
    }

    if (!trimmedEmail.includes('@') || !trimmedEmail.includes('.')) {
      setError('Please enter a valid email address.')
      return
    }

    if (!password) {
      setError('Please enter a password.')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please verify.')
      return
    }

    setIsSubmitting(true)

    try {
      await register({
        display_name: trimmedName,
        email: trimmedEmail,
        password,
      })
      navigate('/app/dashboard', { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 409) {
          setError('An account with this email address already exists. Please log in instead.')
        } else if (err.status === 422) {
          setError(err.detail || 'Validation error. Please check your inputs.')
        } else {
          setError(err.detail || 'Failed to create account. Please try again.')
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
        title="Create account"
        description="Create your LexAssist account."
      />
      <div className="placeholder-stack">
        <Card title="Get started" description="Create a new LexAssist account.">
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
              <label htmlFor="register-name">Full name</label>
              <input
                id="register-name"
                name="name"
                type="text"
                autoComplete="name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Jane Smith"
                required
                disabled={isSubmitting}
              />
            </div>
            <div className="auth-form-field">
              <label htmlFor="register-email">Email</label>
              <input
                id="register-email"
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
              <label htmlFor="register-password">Password</label>
              <input
                id="register-password"
                name="password"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 8 characters"
                required
                disabled={isSubmitting}
              />
            </div>
            <div className="auth-form-field">
              <label htmlFor="register-confirm-password">Confirm password</label>
              <input
                id="register-confirm-password"
                name="confirm_password"
                type="password"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat your password"
                required
                disabled={isSubmitting}
              />
            </div>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating account...' : 'Create account'}
            </Button>
          </form>
          <p className="auth-switch">
            Already have an account? <Link to="/login">Log in</Link>
          </p>
        </Card>
        <DisclaimerBanner />
      </div>
    </div>
  )
}

export default Register
