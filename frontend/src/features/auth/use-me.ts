import { useQuery } from '@tanstack/react-query'

import { api } from '@/services/api'

export function useMe() {
  return useQuery({ queryKey: ['me'], queryFn: api.me })
}

/** The organization the UI operates in. Multi-organization switching is deferred; the first membership is used. */
export function useActiveOrg() {
  const query = useMe()
  return { ...query, org: query.data?.memberships[0] }
}
