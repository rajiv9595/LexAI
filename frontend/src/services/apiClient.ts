/**
 * Typed API client for LexAssist backend endpoints.
 */

import { clearAccessToken, getAccessToken } from './tokenStorage'

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8005'
).replace(/\/+$/, '')

export class ApiError extends Error {
  readonly status: number
  readonly detail: string
  readonly rawErrors?: unknown

  constructor(status: number, detail: string, rawErrors?: unknown) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.rawErrors = rawErrors
  }
}

export interface RequestOptions extends RequestInit {
  /**
   * Explicit bearer token or `null` for unauthenticated requests.
   * If omitted (`undefined`), automatically retrieves the stored token.
   */
  token?: string | null
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  const apiPath = cleanPath.startsWith('/api/v1')
    ? cleanPath
    : `/api/v1${cleanPath}`
  const url = `${API_BASE_URL}${apiPath}`

  const headers = new Headers(options.headers || {})
  headers.set('Accept', 'application/json')

  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  // Token resolution:
  // - undefined: use stored token if available
  // - string: use explicit token
  // - null: do not attach token
  const tokenToUse =
    options.token === undefined ? getAccessToken() : options.token

  if (tokenToUse) {
    headers.set('Authorization', `Bearer ${tokenToUse}`)
  }

  let response: Response
  try {
    response = await fetch(url, {
      ...options,
      headers,
    })
  } catch (error) {
    throw new ApiError(
      0,
      'Unable to connect to the backend server. Please verify the server is running.',
      error,
    )
  }

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`
    let rawErrors: unknown = undefined

    try {
      const data = await response.json()
      if (typeof data.detail === 'string') {
        detail = data.detail
      } else if (Array.isArray(data.detail)) {
        // FastAPI validation errors
        rawErrors = data.detail
        detail = data.detail
          .map(
            (err: { msg?: string; loc?: string[] }) =>
              err.msg || 'Validation error',
          )
          .join(', ')
      } else if (data.detail && typeof data.detail === 'object') {
        rawErrors = data.detail
        detail = JSON.stringify(data.detail)
      }
    } catch {
      // If response body is not JSON, retain default status message
    }

    if (response.status === 401) {
      clearAccessToken()
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('lexassist:unauthorized'))
      }
      if (!detail || detail === `Request failed with status ${response.status}`) {
        detail = 'Your session has expired. Please log in again.'
      }
    }

    throw new ApiError(response.status, detail, rawErrors)
  }

  if (response.status === 204) {
    return undefined as unknown as T
  }

  try {
    return (await response.json()) as T
  } catch {
    return undefined as unknown as T
  }
}
