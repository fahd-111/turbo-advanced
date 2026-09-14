'use client'

import { signOut } from '@/lib/auth-client'
import Link from 'next/link'
import { useState } from 'react'

export function SignInLink() {
  return (
    <Link href="/login" className="cursor-pointer text-purple-600 underline">
      Login
    </Link>
  )
}

export function SignOutLink() {
  const [error, setError] = useState('')
  return (
    <>
      <button
        type="button"
        onClick={() =>
          signOut().catch(() =>
            setError('Unable to sign out. Please try again.')
          )
        }
        className="cursor-pointer text-purple-600 underline"
      >
        Logout
      </button>
      {error && <span role="alert">{error}</span>}
    </>
  )
}

export function PagesOverview() {
  return (
    <ul className="flex flex-col gap-6">
      <li className="flex flex-col gap-4 lg:flex-row lg:items-center">
        <span className="w-40 font-medium">Authenticated pages</span>

        <ul className="flex flex-row gap-6">
          <li>
            <Link href="/profile" className="text-purple-600 underline">
              Profile
            </Link>
          </li>

          <li>
            <Link href="/change-password" className="text-purple-600 underline">
              Change password
            </Link>
          </li>

          <li>
            <Link href="/delete-account" className="text-purple-600 underline">
              Delete account
            </Link>
          </li>
        </ul>
      </li>

      <li className="flex flex-col gap-4 lg:flex-row lg:items-center">
        <span className="w-40 font-medium">Anonymous pages</span>

        <ul className="flex flex-row gap-6">
          <li>
            <SignInLink />
          </li>

          <li>
            <a href="/register" className="text-purple-600 underline">
              Register
            </a>
          </li>

          <li>
            <SignOutLink />
          </li>
        </ul>
      </li>
    </ul>
  )
}
