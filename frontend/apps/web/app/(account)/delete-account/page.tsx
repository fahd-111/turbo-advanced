import { deleteAccountAction } from '@/actions/delete-account-action'
import { DeleteAccountForm } from '@/components/forms/delete-account-form'
import { getCurrentUser } from '@/lib/auth'
import type { Metadata } from 'next'
import { redirect } from 'next/navigation'

export const metadata: Metadata = {
  title: 'Delete account - Turbo'
}

export default async function DeleteAccount() {
  const user = await getCurrentUser()
  if (!user) redirect('/login')
  return (
    <DeleteAccountForm
      username={user.username}
      onSubmitHandler={deleteAccountAction}
    />
  )
}
