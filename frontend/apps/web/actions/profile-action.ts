'use server'

import { ApiError, type UserCurrentError } from '@frontend/types/api'
import type { z } from 'zod'
import { getApiClient } from '@/lib/api'
import { getCurrentUser } from '@/lib/auth'
import type { profileFormSchema } from '@/lib/validation'

export type ProfileFormSchema = z.infer<typeof profileFormSchema>

export async function profileAction(
  data: ProfileFormSchema
): Promise<boolean | UserCurrentError> {
  const user = await getCurrentUser()
  if (!user) return false

  try {
    const apiClient = await getApiClient()

    await apiClient.users.usersMePartialUpdate({
      first_name: data.firstName,
      last_name: data.lastName
    })

    return true
  } catch (error) {
    if (error instanceof ApiError) {
      return error.body as UserCurrentError
    }
  }

  return false
}
