'use server'

import { getApiClient } from '@/lib/api'
import { getCurrentUser } from '@/lib/auth'
import type { deleteAccountFormSchema } from '@/lib/validation'
import { ApiError } from '@frontend/types/api'
import type { z } from 'zod'

export type DeleteAccountFormSchema = z.infer<typeof deleteAccountFormSchema>

export async function deleteAccountAction(
  data: DeleteAccountFormSchema
): Promise<boolean> {
  const user = await getCurrentUser()
  if (!user || data.username !== user.username) return false

  try {
    const apiClient = await getApiClient()

    await apiClient.users.usersDeleteAccountDestroy()
    return true
  } catch (error) {
    if (error instanceof ApiError) {
      return false
    }
  }

  return false
}
