import { twMerge } from 'tailwind-merge'
import { getCurrentUser } from '@/lib/auth'

export async function UserSession() {
  const user = await getCurrentUser()
  const status = user ? 'authenticated' : 'unauthenticated'

  return (
    <ul className="flex flex-col gap-4">
      <li className="flex items-center gap-4">
        <span className="w-40 font-medium">Session</span>
        <span
          className={twMerge(
            'rounded bg-white px-2 py-1.5 leading-none shadow-sm outline outline-1 outline-gray-900/10',
            status === 'authenticated' &&
              'bg-green-100 text-green-800 outline-green-700/30'
          )}
        >
          {status}
        </span>
      </li>

      <li className="flex items-center gap-4">
        <span className="w-40 font-medium">Username</span>
        <span className="rounded bg-white px-2 py-1.5 leading-none shadow-sm outline outline-1 outline-gray-900/10">
          {user?.username || 'undefined'}
        </span>
      </li>
    </ul>
  )
}
