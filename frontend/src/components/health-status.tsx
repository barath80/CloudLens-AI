import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/services/api'

import { ErrorState, LoadingState } from './state-views'

export function HealthStatus() {
  const query = useQuery({
    queryKey: ['health', 'ready'],
    queryFn: ({ signal }) => api.ready(signal),
    refetchInterval: 30_000,
    retry: 1,
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>System status</CardTitle>
      </CardHeader>
      <CardContent>
        {query.isPending && <LoadingState label="Checking backend status" />}
        {query.isError && <ErrorState error={query.error} onRetry={() => void query.refetch()} title="Backend unavailable" />}
        {query.isSuccess && (
          <ul className="space-y-2 text-sm" aria-label="Backend dependency checks">
            <li className="flex items-center justify-between">
              <span>API</span>
              <Badge variant={query.data.status === 'ready' ? 'default' : 'destructive'}>{query.data.status.replace('_', ' ')}</Badge>
            </li>
            {Object.entries(query.data.checks).map(([name, state]) => (
              <li key={name} className="flex items-center justify-between">
                <span className="capitalize">{name}</span>
                <Badge variant={state === 'ok' ? 'secondary' : 'destructive'}>{state}</Badge>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
