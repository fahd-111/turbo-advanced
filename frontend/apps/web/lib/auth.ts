import { ApiError } from '@frontend/types/api'
import { cache } from 'react'
import { getApiClient } from './api'

export const getCurrentUser = cache(async () => {
  const apiClient = await getApiClient()
  try {
    return await apiClient.users.usersMeRetrieve()
  } catch (error) {
    if (error instanceof ApiError && [401, 403].includes(error.status)) {
      return null
    }
    throw error
  }
})
