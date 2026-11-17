import { lazy, Suspense } from 'react'

import { HealthStatus } from '@/components/health-status'
import { LoadingState, PageHeader } from '@/components/state-views'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useActiveOrg } from '@/features/auth/use-me'

const TimeSeriesChart = lazy(() => import('@/components/time-series-chart'))

// Illustrative shape only. Not customer data; shown to preview the chart layout.
const DEMO_SERIES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((label, i) => ({
  label,
  value: [3, 5, 4, 6, 5, 7, 6][i] ?? 0,
}))

const KPIS = ['Month-to-date spend', 'Estimated savings', 'Realized savings']

export default function DashboardPage() {
  const { org } = useActiveOrg()
  return (
    <>
      <PageHeader title="Dashboard" description={org ? `Overview for ${org.organization_name}` : undefined} />
      <div className="grid gap-4 sm:grid-cols-3">
        {KPIS.map((label) => (
          <Card key={label}>
            <CardHeader>
              <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold">—</p>
              <p className="mt-1 text-xs text-muted-foreground">No billing data connected yet</p>
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Spend trend <Badge variant="outline">Demo placeholder</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Suspense fallback={<LoadingState label="Loading chart" />}>
              <TimeSeriesChart data={DEMO_SERIES} ariaLabel="Demo placeholder chart, not real spend data" />
            </Suspense>
          </CardContent>
        </Card>
        <HealthStatus />
      </div>
    </>
  )
}
