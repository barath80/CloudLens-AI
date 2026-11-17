import { EmptyState, PageHeader } from '@/components/state-views'
import { useAuth } from '@/features/auth/auth-context'
import { useMe } from '@/features/auth/use-me'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function BillingPage() {
  return (
    <>
      <PageHeader title="Billing Overview" description="Actual AWS billing data from CUR 2.0 exports." />
      <EmptyState
        title="Billing import not available yet"
        description="CUR 2.0 ingestion is planned for a later stage. Nothing is imported or calculated today."
      />
    </>
  )
}

export function InventoryPage() {
  return (
    <>
      <PageHeader title="Resource Inventory" description="Discovered EC2, EBS and S3 resources." />
      <EmptyState
        title="Inventory discovery not available yet"
        description="Resource discovery through STS AssumeRole is planned for a later stage."
      />
    </>
  )
}

export function RecommendationsPage() {
  return (
    <>
      <PageHeader title="Recommendations" description="Evidence-backed optimization recommendations." />
      <EmptyState
        title="No recommendations yet"
        description="The deterministic optimization engine is not built yet. No recommendation is ever applied without explicit human approval."
      />
    </>
  )
}

export function SettingsPage() {
  const me = useMe()
  const { logout } = useAuth()
  return (
    <>
      <PageHeader title="Settings" />
      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>
            <span className="text-muted-foreground">Name:</span> {me.data?.user.full_name}
          </p>
          <p>
            <span className="text-muted-foreground">Email:</span> {me.data?.user.email}
          </p>
          {me.data?.memberships.map((m) => (
            <p key={m.organization_id}>
              <span className="text-muted-foreground">Organization:</span> {m.organization_name} ({m.role})
            </p>
          ))}
          <Button variant="outline" onClick={logout}>
            Sign out
          </Button>
        </CardContent>
      </Card>
    </>
  )
}
