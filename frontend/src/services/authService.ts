/**
 * Authentication service communicating with FastAPI auth endpoints.
 */

import { apiRequest } from './apiClient'
import { getAccessToken } from './tokenStorage'
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
} from '../types/auth'

export async function register(payload: RegisterRequest): Promise<User> {
  return apiRequest<User>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function login(payload: LoginRequest): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getCurrentUser(tokenOverride?: string): Promise<User> {
  const token = tokenOverride ?? getAccessToken()
  if (!token) {
    throw new Error('No access token available.')
  }
  return apiRequest<User>('/api/v1/auth/me', {
    method: 'GET',
    token,
  })
}
