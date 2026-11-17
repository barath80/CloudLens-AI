import { createBrowserRouter } from 'react-router'

import { AuthLayout } from '@/layouts/AuthLayout'
import { AppShell } from '@/layouts/AppShell'
import LoginPage from '@/features/auth/LoginPage'
import RegisterPage from '@/features/auth/RegisterPage'
import CloudAccountsPage from '@/features/cloud-accounts/CloudAccountsPage'
import DashboardPage from '@/features/dashboard/DashboardPage'
import {
  BillingPage,
  InventoryPage,
  RecommendationsPage,
  SettingsPage,
} from '@/features/placeholders/PlaceholderPages'

export const routes = [
  {
    element: <AuthLayout />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
    ],
  },
  {
    element: <AppShell />,
    children: [
      { path: '/', element: <DashboardPage /> },
      { path: '/cloud-accounts', element: <CloudAccountsPage /> },
      { path: '/billing', element: <BillingPage /> },
      { path: '/inventory', element: <InventoryPage /> },
      { path: '/recommendations', element: <RecommendationsPage /> },
      { path: '/settings', element: <SettingsPage /> },
    ],
  },
]

export const router = createBrowserRouter(routes)
