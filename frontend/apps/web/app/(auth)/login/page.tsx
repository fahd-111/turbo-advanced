import type { Metadata } from 'next'
import { LoginForm } from '@/components/forms/login-form'

export const metadata: Metadata = {
  title: 'Login - Turbo'
}

export default function Login() {
  return <LoginForm />
}
