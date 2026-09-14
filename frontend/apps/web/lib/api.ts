import { ApiClient } from '@frontend/types/api'
import { cookies } from 'next/headers'

export async function getAuthenticationHeaders() {
  const cookieStore = await cookies()
  return {
    Cookie: ['sessionid', 'csrftoken']
      .map((name) => `${name}=${cookieStore.get(name)?.value ?? ''}`)
      .join('; '),
    'X-CSRFToken': cookieStore.get('csrftoken')?.value ?? ''
  }
}

export async function getApiClient() {
  return new ApiClient({
    BASE: process.env.API_URL,
    HEADERS: {
      ...(await getAuthenticationHeaders()),
      Referer: `${process.env.API_URL}/`
    }
  })
}
