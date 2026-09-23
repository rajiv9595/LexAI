/**
 * Authentication Context and Provider for React application.
 */

import {
  createContext,
  useCallback,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import * as authService from '../services/authService'
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from '../services/tokenStorage'
import type { LoginRequest, RegisterRequest, User } from '../types/auth'

export interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  register: (payload: RegisterRequest) => Promise<void>
  logout: () => void
  refreshCurrentUser: () => Promise<User | null>
}

export const AuthContext = createContext<AuthContextValue | undefined>(
  undefined,
)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  const refreshCurrentUser = useCallback(async (): Promise<User | null> => {
    const token = getAccessToken()
    if (!token) {
      setUser(null)
      setIsAuthenticated(false)
      setIsLoading(false)
      return null
    }

    try {
      const profile = await authService.getCurrentUser(token)
      setUser(profile)
      setIsAuthenticated(true)
      return profile
    } catch {
      clearAccessToken()
      setUser(null)
      setIsAuthenticated(false)
      return null
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void refreshCurrentUser()

    const handleUnauthorized = () => {
      setUser(null)
      setIsAuthenticated(false)
      setIsLoading(false)
    }

    window.addEventListener('lexassist:unauthorized', handleUnauthorized)
    return () => {
      window.removeEventListener('lexassist:unauthorized', handleUnauthorized)
    }
  }, [refreshCurrentUser])

  const login = useCallback(async (credentials: LoginRequest): Promise<void> => {
    const tokenResp = await authService.login(credentials)
    setAccessToken(tokenResp.access_token)
    const profile = await authService.getCurrentUser(tokenResp.access_token)
    setUser(profile)
    setIsAuthenticated(true)
  }, [])

  const register = useCallback(
    async (payload: RegisterRequest): Promise<void> => {
      await authService.register(payload)
      // Automatically log in with the new credentials
      const tokenResp = await authService.login({
        email: payload.email,
        password: payload.password,
      })
      setAccessToken(tokenResp.access_token)
      const profile = await authService.getCurrentUser(tokenResp.access_token)
      setUser(profile)
      setIsAuthenticated(true)
    },
    [],
  )

  const logout = useCallback((): void => {
    clearAccessToken()
    setUser(null)
    setIsAuthenticated(false)
  }, [])

  const value: AuthContextValue = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshCurrentUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
