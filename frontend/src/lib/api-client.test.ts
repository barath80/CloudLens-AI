import { z } from 'zod'

import { ApiError, apiRequest, configureApiClient } from './api-client'

const schema = z.object({ ok: z.boolean() })

function mockFetch(response: Response | Error) {
  const fn = vi.fn(async () => {
    if (response instanceof Error) throw response
    return response
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

afterEach(() => {
  vi.unstubAllGlobals()
  configureApiClient({ getToken: () => null, onUnauthorized: () => {} })
})

describe('apiRequest', () => {
  it('returns validated data and attaches the bearer token', async () => {
    configureApiClient({ getToken: () => 'tok', onUnauthorized: () => {} })
    const fetchMock = mockFetch(json({ ok: true }))
    await expect(apiRequest('/x', { schema })).resolves.toEqual({ ok: true })
    const init = (fetchMock.mock.calls[0] as unknown as [string, RequestInit])[1]
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer tok')
  })

  it('normalises backend errors', async () => {
    mockFetch(json({ error: { code: 'validation_error', message: 'bad', details: [{ field: 'a', message: 'm' }] } }, 422))
    const err = await apiRequest('/x', { schema }).catch((e: unknown) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err).toMatchObject({ status: 422, code: 'validation_error', details: [{ field: 'a', message: 'm' }] })
  })

  it('rejects responses that do not match the schema', async () => {
    mockFetch(json({ ok: 'yes' }))
    await expect(apiRequest('/x', { schema })).rejects.toMatchObject({ code: 'invalid_response' })
  })

  it('maps network failures to a friendly error', async () => {
    mockFetch(new TypeError('failed'))
    await expect(apiRequest('/x', { schema })).rejects.toMatchObject({ status: 0, code: 'network_error' })
  })

  it('signs out on 401 when authenticated, but not for login attempts', async () => {
    const onUnauthorized = vi.fn()
    configureApiClient({ getToken: () => 'tok', onUnauthorized })
    mockFetch(json({ error: { code: 'unauthorized', message: 'no' } }, 401))
    await apiRequest('/x', { schema }).catch(() => {})
    expect(onUnauthorized).toHaveBeenCalledTimes(1)
    await apiRequest('/x', { schema, skipAuthRedirect: true }).catch(() => {})
    expect(onUnauthorized).toHaveBeenCalledTimes(1)
  })

  it('handles 204 without a schema', async () => {
    mockFetch(new Response(null, { status: 204 }))
    await expect(apiRequest('/x', { method: 'DELETE' })).resolves.toBeUndefined()
  })
})
