import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { EmptyState, ErrorState, LoadingState, PageHeader } from '@/components/state-views'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useActiveOrg } from '@/features/auth/use-me'
import { ApiError } from '@/lib/api-client'
import { api } from '@/services/api'

const schema = z.object({
  name: z.string().trim().min(1, 'Enter a name').max(200),
  account_id: z.string().regex(/^\d{12}$/, 'Must be a 12-digit AWS account ID'),
  role_arn: z.string().regex(/^arn:aws[a-z-]*:iam::\d{12}:role\/[\w+=,.@/-]+$/, 'Must be an IAM role ARN'),
})
type Values = z.infer<typeof schema>

export default function CloudAccountsPage() {
  const { org } = useActiveOrg()
  const orgId = org?.organization_id ?? ''
  const canWrite = org?.role === 'owner' || org?.role === 'admin'
  const queryClient = useQueryClient()
  const key = ['cloud-accounts', orgId]

  const list = useQuery({ queryKey: key, queryFn: () => api.listCloudAccounts(orgId), enabled: !!orgId })
  const create = useMutation({
    mutationFn: (v: Values) => api.createCloudAccount(orgId, v),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: key }),
  })
  const remove = useMutation({
    mutationFn: (id: string) => api.deleteCloudAccount(orgId, id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: key }),
  })

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<Values>({ resolver: zodResolver(schema) })

  const onSubmit = handleSubmit((values) => create.mutate(values, { onSuccess: () => reset() }))

  return (
    <>
      <PageHeader
        title="Cloud Accounts"
        description="Register AWS accounts. CloudLens connects through a read-only cross-account IAM role you create; no access keys are stored."
      />
      {canWrite && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Add AWS account</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-3" noValidate>
              {(
                [
                  ['name', 'Name', 'Production'],
                  ['account_id', 'AWS account ID', '123456789012'],
                  ['role_arn', 'Role ARN', 'arn:aws:iam::123456789012:role/CloudLensReadOnly'],
                ] as const
              ).map(([field, label, placeholder]) => (
                <div key={field} className="space-y-1.5">
                  <Label htmlFor={field}>{label}</Label>
                  <Input id={field} placeholder={placeholder} aria-invalid={!!errors[field]} {...register(field)} />
                  {errors[field] && <p className="text-sm text-destructive">{errors[field]?.message}</p>}
                </div>
              ))}
              <div className="md:col-span-3">
                {create.isError && (
                  <Alert variant="destructive" className="mb-3">
                    <AlertDescription>
                      {create.error instanceof ApiError ? create.error.message : 'Could not add the account.'}
                    </AlertDescription>
                  </Alert>
                )}
                <Button type="submit" disabled={create.isPending}>
                  {create.isPending ? 'Adding…' : 'Add account'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {list.isPending && <LoadingState label="Loading cloud accounts" />}
      {list.isError && <ErrorState error={list.error} onRetry={() => void list.refetch()} />}
      {list.isSuccess && list.data.length === 0 && (
        <EmptyState
          title="No cloud accounts yet"
          description={canWrite ? 'Add an AWS account above to begin.' : 'Ask an owner or admin to connect an AWS account.'}
        />
      )}
      {list.isSuccess && list.data.length > 0 && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Account ID</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>External ID</TableHead>
              {canWrite && <TableHead className="text-right">Actions</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {list.data.map((a) => (
              <TableRow key={a.id}>
                <TableCell>{a.name}</TableCell>
                <TableCell className="font-mono">{a.account_id}</TableCell>
                <TableCell>
                  <Badge variant="secondary">{a.status}</Badge>
                </TableCell>
                <TableCell className="font-mono text-xs">{a.external_id}</TableCell>
                {canWrite && (
                  <TableCell className="text-right">
                    <Button
                      variant="destructive"
                      size="sm"
                      disabled={remove.isPending}
                      aria-label={`Remove ${a.name}`}
                      onClick={() => remove.mutate(a.id)}
                    >
                      Remove
                    </Button>
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </>
  )
}
