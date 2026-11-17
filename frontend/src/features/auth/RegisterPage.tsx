import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router'
import { z } from 'zod'

import { errorMessage } from '@/components/state-views'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

import { useAuth } from './auth-context'

// Mirrors backend limits; the backend remains authoritative.
export const registerSchema = z.object({
  full_name: z.string().trim().min(1, 'Enter your name').max(200),
  organization_name: z.string().trim().min(1, 'Enter an organization name').max(200),
  email: z.email('Enter a valid email address'),
  password: z.string().min(12, 'Use at least 12 characters').max(128),
})
type Values = z.infer<typeof registerSchema>

const FIELDS: { name: keyof Values; label: string; type: string; autoComplete: string }[] = [
  { name: 'full_name', label: 'Full name', type: 'text', autoComplete: 'name' },
  { name: 'organization_name', label: 'Organization', type: 'text', autoComplete: 'organization' },
  { name: 'email', label: 'Email', type: 'email', autoComplete: 'email' },
  { name: 'password', label: 'Password (12+ characters)', type: 'password', autoComplete: 'new-password' },
]

export default function RegisterPage() {
  const { register: signUp } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(registerSchema) })

  const onSubmit = handleSubmit(async (values) => {
    setError(null)
    try {
      await signUp(values)
      void navigate('/', { replace: true })
    } catch (e) {
      setError(errorMessage(e))
    }
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle render={<h1 />}>Create your account</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {FIELDS.map(({ name, label, type, autoComplete }) => (
            <div key={name} className="space-y-1.5">
              <Label htmlFor={name}>{label}</Label>
              <Input id={name} type={type} autoComplete={autoComplete} aria-invalid={!!errors[name]} {...register(name)} />
              {errors[name] && <p className="text-sm text-destructive">{errors[name]?.message}</p>}
            </div>
          ))}
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Creating account…' : 'Create account'}
          </Button>
          <p className="text-center text-sm text-muted-foreground">
            Already registered?{' '}
            <Link to="/login" className="underline underline-offset-4">
              Sign in
            </Link>
          </p>
        </form>
      </CardContent>
    </Card>
  )
}
