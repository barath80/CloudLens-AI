import type { ZodType } from 'zod'

export const API_BASE_URL: string = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1').replace(
  /\/$/,
  '',
)

export interface FieldIssue {
  field: string
  message: string
}

/** Normalised error for every failed request, including network and malformed-response failures. */
export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: FieldIssue[]

  constructor(status: number, code: string, message: string, details: FieldIssue[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

type TokenGetter = () => string | null
let getToken: TokenGetter = () => null
let onUnauthorized: () => void = () => {}

/** Called once by the auth provider so the client can attach tokens and react to expired sessions. */
export function configureApiClient(opts: { getToken: TokenGetter; onUnauthorized: () => void }): void {
  getToken = opts.getToken
  onUnauthorized = opts.onUnauthorized
}

interface RequestOptions<T> {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  /** Response schema. Omit only for empty (204) responses. */
  schema?: ZodType<T>
  signal?: AbortSignal
  /** Skip the global 401 handler (e.g. a failed login is not an expired session). */
  skipAuthRedirect?: boolean
}

export async function apiRequest<T = void>(path: string, opts: RequestOptions<T> = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (opts.body !== undefined) headers['Content-Type'] = 'application/json'

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: opts.method ?? 'GET',
      headers,
      body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
      signal: opts.signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError(0, 'network_error', 'Unable to reach the CloudLens API. Check your connection and try again.')
  }

  if (!response.ok) {
    const error = await parseError(response)
    if (response.status === 401 && token && !opts.skipAuthRedirect) onUnauthorized()
    throw error
  }

  if (response.status === 204 || !opts.schema) return undefined as T

  const parsed = opts.schema.safeParse(await response.json().catch(() => undefined))
  if (!parsed.success) {
    throw new ApiError(response.status, 'invalid_response', 'The server returned an unexpected response.')
  }
  return parsed.data
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as { error?: { code?: string; message?: string; details?: FieldIssue[] } }
    const e = body.error
    return new ApiError(response.status, e?.code ?? 'http_error', e?.message ?? response.statusText, e?.details ?? [])
  } catch {
    return new ApiError(response.status, 'http_error', response.statusText || 'Request failed')
  }
}
