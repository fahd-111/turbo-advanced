import { getAuthenticationHeaders } from '@/lib/api'
import type { NextRequest } from 'next/server'

async function proxyAuthentication(
  request: NextRequest,
  context: { params: Promise<{ action: string }> }
) {
  const { action } = await context.params
  const allowedMethods: Record<string, string> = {
    csrf: 'GET',
    login: 'POST',
    logout: 'POST'
  }
  const allowedMethod = Object.hasOwn(allowedMethods, action)
    ? allowedMethods[action]
    : undefined
  if (!allowedMethod) return new Response(null, { status: 404 })
  if (request.method !== allowedMethod) {
    return new Response(null, {
      status: 405,
      headers: { Allow: allowedMethod }
    })
  }

  const response = await fetch(`${process.env.API_URL}/api/auth/${action}/`, {
    method: request.method,
    headers: {
      ...(await getAuthenticationHeaders()),
      'Content-Type': 'application/x-www-form-urlencoded',
      // Django validates the browser's CSRF header and origin, including login.
      'X-CSRFToken': request.headers.get('x-csrftoken') ?? '',
      Origin: request.headers.get('origin') ?? '',
      Referer: request.headers.get('referer') ?? ''
    },
    body: request.method === 'POST' ? await request.text() : undefined,
    cache: 'no-store',
    redirect: 'manual'
  })
  const headers = new Headers({
    'Content-Type': response.headers.get('content-type') ?? 'application/json',
    'Cache-Control': 'no-store'
  })
  response.headers
    .getSetCookie()
    .map((cookie) => headers.append('Set-Cookie', cookie))
  return new Response(response.body, { status: response.status, headers })
}

export { proxyAuthentication as GET, proxyAuthentication as POST }
