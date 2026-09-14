import type { Metadata } from 'next'
import { registerAction } from '@/actions/register-action'
import { RegisterForm } from '@/components/forms/register-form'

export const metadata: Metadata = {
  title: 'Register - Turbo'
}

export default function Register() {
  return <RegisterForm onSubmitHandler={registerAction} />
}
