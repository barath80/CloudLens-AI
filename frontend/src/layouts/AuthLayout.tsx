import { Navigate, Outlet } from 'react-router'

import { useAuth } from '@/features/auth/auth-context'

export function AuthLayout() {
  const { isAuthenticated } = useAuth()
  if (isAuthenticated) return <Navigate to="/" replace />
  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/40 px-4 py-10">
      <div className="w-full max-w-md">
        <p className="mb-6 text-center text-xl font-semibold tracking-tight">CloudLens AI</p>
        <Outlet />
      </div>
    </main>
  )
}
