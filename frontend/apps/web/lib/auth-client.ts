export async function submitAuthentication(
  action: 'login' | 'logout',
  credentials?: { username: string; password: string }
) {
  const csrfResponse = await fetch('/api/auth/csrf', { cache: 'no-store' })
  if (!csrfResponse.ok) throw new Error('Unable to contact the login service.')
  const { csrfToken } = await csrfResponse.json()
  return fetch(`/api/auth/${action}`, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken },
    body: new URLSearchParams(credentials)
  })
}

export async function signOut() {
  const response = await submitAuthentication('logout')
  if (!response.ok) throw new Error('Unable to sign out. Please try again.')
  window.location.assign('/login')
}
