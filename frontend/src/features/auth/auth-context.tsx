import { useQueryClient } from '@tanstack/react-query'
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

import { configureApiClient } from '@/lib/api-client'
import { api, type RegisterInput } from '@/services/api'

// The token lives in sessionStorage (cleared when the tab closes). It is readable by any script on
// the page, so XSS hardening matters; moving to an httpOnly cookie is a tracked hardening item.
const TOKEN_KEY = 'cloudlens.token'

function readToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

function writeToken(token: string | null): void {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token)
    else sessionStorage.removeItem(TOKEN_KEY)
  } catch {
    // Storage unavailable (private mode): the session simply will not survive a reload.
  }
}

interface AuthContextValue {
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (input: RegisterInput) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [token, setToken] = useState<string | null>(readToken)

  const updateToken = useCallback((next: string | null) => {
    writeToken(next)
    setToken(next)
  }, [])

  const logout = useCallback(() => {
    updateToken(null)
    queryClient.clear()
  }, [queryClient, updateToken])

  // Configure synchronously during render so child queries never fire before the client is wired up.
  configureApiClient({ getToken: readToken, onUnauthorized: logout })

  useEffect(() => {
    const onStorage = () => setToken(readToken())
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: token !== null,
      login: async (email, password) => updateToken((await api.login(email, password)).access_token),
      register: async (input) => updateToken((await api.register(input)).access_token),
      logout,
    }),
    [token, updateToken, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
