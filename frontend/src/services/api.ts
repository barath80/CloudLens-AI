import { apiRequest } from '@/lib/api-client'
import {
  cloudAccountListSchema,
  cloudAccountSchema,
  healthSchema,
  meSchema,
  readySchema,
  tokenSchema,
} from '@/types/api'

export interface RegisterInput {
  email: string
  password: string
  full_name: string
  organization_name: string
}

export interface CloudAccountInput {
  name: string
  account_id: string
  role_arn: string
}

export const api = {
  health: (signal?: AbortSignal) => apiRequest('/health', { schema: healthSchema, signal }),
  // The readiness endpoint answers 503 with a body when a dependency is down; surface that as an error.
  ready: (signal?: AbortSignal) => apiRequest('/health/ready', { schema: readySchema, signal }),
  login: (email: string, password: string) =>
    apiRequest('/auth/login', { method: 'POST', body: { email, password }, schema: tokenSchema, skipAuthRedirect: true }),
  register: (input: RegisterInput) =>
    apiRequest('/auth/register', { method: 'POST', body: input, schema: tokenSchema, skipAuthRedirect: true }),
  me: () => apiRequest('/auth/me', { schema: meSchema }),
  listCloudAccounts: (orgId: string) =>
    apiRequest(`/organizations/${orgId}/cloud-accounts`, { schema: cloudAccountListSchema }),
  createCloudAccount: (orgId: string, input: CloudAccountInput) =>
    apiRequest(`/organizations/${orgId}/cloud-accounts`, { method: 'POST', body: input, schema: cloudAccountSchema }),
  deleteCloudAccount: (orgId: string, id: string) =>
    apiRequest(`/organizations/${orgId}/cloud-accounts/${id}`, { method: 'DELETE' }),
}
