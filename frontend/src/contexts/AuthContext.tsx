import { createContext, useContext, type ReactNode } from 'react'
import { useAuth, useLogout } from '../hooks/useAuth'
import type { UserInfo } from '../types/api'

interface AuthContextValue {
  isAuthenticated: boolean
  isAdmin: boolean
  user: UserInfo | null
  oidcEnabled: boolean
  isLoading: boolean
  login: () => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const { data: authStatus, isLoading } = useAuth()
  const logoutMutation = useLogout()

  const login = () => {
    window.location.href = '/auth/login'
  }

  const logout = () => {
    logoutMutation.mutate()
  }

  const value: AuthContextValue = {
    isAuthenticated: authStatus?.authenticated ?? false,
    isAdmin: authStatus?.user?.is_admin ?? false,
    user: authStatus?.user ?? null,
    oidcEnabled: authStatus?.oidc_enabled ?? false,
    isLoading,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuthContext() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider')
  }
  return context
}
