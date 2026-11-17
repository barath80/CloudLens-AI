import { z } from 'zod'

// Runtime schemas for backend responses: network data is untrusted, so it is validated, not just typed.

export const roleSchema = z.enum(['owner', 'admin', 'member', 'viewer'])
export type Role = z.infer<typeof roleSchema>

export const tokenSchema = z.object({ access_token: z.string(), token_type: z.string() })

export const meSchema = z.object({
  user: z.object({ id: z.string(), email: z.string(), full_name: z.string() }),
  memberships: z.array(
    z.object({
      organization_id: z.string(),
      organization_name: z.string(),
      organization_slug: z.string(),
      role: roleSchema,
    }),
  ),
})
export type Me = z.infer<typeof meSchema>

export const healthSchema = z.object({ status: z.literal('ok'), service: z.string(), environment: z.string() })
export const readySchema = z.object({
  status: z.enum(['ready', 'not_ready']),
  checks: z.record(z.string(), z.enum(['ok', 'failed'])),
})
export type Readiness = z.infer<typeof readySchema>
export type Health = z.infer<typeof healthSchema>

export const cloudAccountSchema = z.object({
  id: z.string(),
  organization_id: z.string(),
  provider: z.literal('aws'),
  name: z.string(),
  account_id: z.string(),
  role_arn: z.string(),
  external_id: z.string(),
  status: z.enum(['pending', 'connected', 'error', 'disabled']),
  created_at: z.string(),
})
export type CloudAccount = z.infer<typeof cloudAccountSchema>
export const cloudAccountListSchema = z.array(cloudAccountSchema)
