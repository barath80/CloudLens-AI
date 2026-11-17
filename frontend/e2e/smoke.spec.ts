import { expect, test } from '@playwright/test'

const ME = {
  user: { id: 'u1', email: 'a@example.com', full_name: 'Ada' },
  memberships: [{ organization_id: 'o1', organization_name: 'Acme', organization_slug: 'acme', role: 'owner' }],
}

test('unauthenticated visitors are sent to the sign-in page', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
})

test('signed-in users can navigate between sections', async ({ page }) => {
  await page.addInitScript(() => sessionStorage.setItem('cloudlens.token', 'test-token'))
  await page.route('**/api/v1/auth/me', (r) => r.fulfill({ json: ME }))
  await page.route('**/api/v1/health/ready', (r) => r.fulfill({ json: { status: 'ready', checks: { database: 'ok' } } }))
  await page.route('**/api/v1/organizations/o1/cloud-accounts', (r) => r.fulfill({ json: [] }))

  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
  await expect(page.getByText('Demo placeholder')).toBeVisible()

  await page.getByRole('link', { name: 'Cloud Accounts' }).click()
  await expect(page.getByRole('heading', { name: 'Cloud Accounts' })).toBeVisible()
  await expect(page.getByText('No cloud accounts yet')).toBeVisible()
})
