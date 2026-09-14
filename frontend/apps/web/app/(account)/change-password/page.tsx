import type { Metadata } from 'next'
import { changePasswordAction } from '@/actions/change-password-action'
import { ChangePaswordForm } from '@/components/forms/change-password-form'

export const metadata: Metadata = {
  title: 'Change password - Turbo'
}

export default function ChangePassword() {
  return <ChangePaswordForm onSubmitHandler={changePasswordAction} />
}
