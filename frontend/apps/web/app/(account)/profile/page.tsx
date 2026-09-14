import type { Metadata } from 'next'
import { profileAction } from '@/actions/profile-action'
import { ProfileForm } from '@/components/forms/profile-form'
import { getApiClient } from '@/lib/api'

export const metadata: Metadata = {
  title: 'Profile - Turbo'
}

export default async function Profile() {
  const apiClient = await getApiClient()

  return (
    <ProfileForm
      currentUser={apiClient.users.usersMeRetrieve()}
      onSubmitHandler={profileAction}
    />
  )
}
