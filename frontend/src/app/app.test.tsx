import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { routes } from '@/app/router'
import { renderRoutes } from '@/test/render'

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

const ME = {
  user: { id: 'u1', email: 'a@example.com', full_name: 'Ada' },
  memberships: [{ organization_id: 'o1', organization_name: 'Acme', organization_slug: 'acme', role: 'owner' }],
}

beforeEach(() => sessionStorage.clear())
afterEach(() => vi.unstubAllGlobals())

describe('routing', () => {
  it('redirects unauthenticated users to login', async () => {
    renderRoutes(routes, '/cloud-accounts')
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('shows the app shell and navigation for authenticated users', async () => {
    sessionStorage.setItem('cloudlens.token', 't')
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (url.endsWith('/auth/me')) return json(ME)
        if (url.endsWith('/cloud-accounts')) return json([])
        return json({ status: 'ready', checks: { database: 'ok' } })
      }),
    )
    renderRoutes(routes, '/')
    expect(await screen.findByRole('heading', { name: 'Dashboard' })).toBeInTheDocument()
    const nav = screen.getByRole('navigation', { name: 'Primary' })
    for (const name of ['Dashboard', 'Cloud Accounts', 'Billing Overview', 'Resource Inventory', 'Recommendations', 'Settings']) {
      expect(nav).toHaveTextContent(name)
    }
    expect(await screen.findByText('Demo placeholder')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('link', { name: /Cloud Accounts/ }))
    expect(await screen.findByText('No cloud accounts yet')).toBeInTheDocument()
  })

  it('shows an error state when the workspace cannot load', async () => {
    sessionStorage.setItem('cloudlens.token', 't')
    vi.stubGlobal('fetch', vi.fn(async () => json({ error: { code: 'internal_error', message: 'Boom' } }, 500)))
    renderRoutes(routes, '/')
    expect(await screen.findByText('Unable to load your workspace')).toBeInTheDocument()
    expect(screen.getByText('Boom')).toBeInTheDocument()
  })
})

describe('forms', () => {
  it('validates registration input client-side before calling the API', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    renderRoutes(routes, '/register')
    await userEvent.type(await screen.findByLabelText('Email'), 'not-an-email')
    await userEvent.type(screen.getByLabelText(/Password/), 'short')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByText('Use at least 12 characters')).toBeInTheDocument()
    expect(screen.getByText('Enter a valid email address')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('shows the server error on a failed login', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => json({ error: { code: 'unauthorized', message: 'Incorrect email or password' } }, 401)),
    )
    renderRoutes(routes, '/login')
    await userEvent.type(await screen.findByLabelText('Email'), 'a@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'whatever-pass')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Incorrect email or password'))
  })
})
