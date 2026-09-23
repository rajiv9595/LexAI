/**
 * Authentication type definitions matching the backend API contracts.
 * Never stores or exposes password hashes.
 */

export interface User {
  id: string
  email: string
  display_name: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface RegisterRequest {
  email: string
  password: string
  display_name: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}
