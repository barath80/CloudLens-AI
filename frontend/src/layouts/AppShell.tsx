import { Cloud, CreditCard, LayoutDashboard, LogOut, Server, Settings, Sparkles } from 'lucide-react'
import { NavLink, Navigate, Outlet } from 'react-router'

import { ErrorState, LoadingState } from '@/components/state-views'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/features/auth/auth-context'
import { useMe } from '@/features/auth/use-me'
import { cn } from '@/lib/utils'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/cloud-accounts', label: 'Cloud Accounts', icon: Cloud },
  { to: '/billing', label: 'Billing Overview', icon: CreditCard },
  { to: '/inventory', label: 'Resource Inventory', icon: Server },
  { to: '/recommendations', label: 'Recommendations', icon: Sparkles },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export function AppShell() {
  const { isAuthenticated, logout } = useAuth()
  const me = useMe()
  if (!isAuthenticated) return <Navigate to="/login" replace />

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:bg-background focus:p-2">
        Skip to content
      </a>
      <aside className="border-b bg-card md:w-64 md:shrink-0 md:border-r md:border-b-0">
        <div className="flex items-center justify-between px-4 py-3 md:block md:px-5 md:py-5">
          <span className="text-lg font-semibold tracking-tight">CloudLens AI</span>
          {me.data?.memberships[0] && (
            <p className="hidden truncate text-xs text-muted-foreground md:mt-1 md:block">
              {me.data.memberships[0].organization_name}
            </p>
          )}
        </div>
        <nav aria-label="Primary" className="flex gap-1 overflow-x-auto px-2 pb-2 md:flex-col md:overflow-visible md:pb-0">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2 rounded-lg px-3 py-2 text-sm whitespace-nowrap transition-colors hover:bg-muted',
                  isActive ? 'bg-muted font-medium text-foreground' : 'text-muted-foreground',
                )
              }
            >
              <Icon className="size-4" aria-hidden />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-end gap-3 border-b px-4 py-2 md:px-8">
          <span className="truncate text-sm text-muted-foreground">{me.data?.user.email}</span>
          <Button variant="outline" size="sm" onClick={logout}>
            <LogOut aria-hidden /> Sign out
          </Button>
        </header>
        <main id="main" className="flex-1 px-4 py-6 md:px-8">
          {me.isPending && <LoadingState label="Loading your workspace" />}
          {me.isError && (
            <ErrorState error={me.error} onRetry={() => void me.refetch()} title="Unable to load your workspace" />
          )}
          {me.isSuccess && <Outlet />}
        </main>
      </div>
    </div>
  )
}
