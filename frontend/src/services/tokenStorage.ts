/**
 * Token storage utility using sessionStorage.
 * Stores only the access token under a dedicated key.
 * Never logs or exposes the token in client console.
 */

const ACCESS_TOKEN_KEY = 'lexassist_access_token'

export function getAccessToken(): string | null {
  try {
    return sessionStorage.getItem(ACCESS_TOKEN_KEY)
  } catch {
    return null
  }
}

export function setAccessToken(token: string): void {
  try {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, token)
  } catch {
    // Gracefully handle storage errors (e.g. private browsing restrictions)
  }
}

export function clearAccessToken(): void {
  try {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY)
  } catch {
    // Gracefully handle storage errors
  }
}
