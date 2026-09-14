'use client'

import type { PropsWithChildren } from 'react'

export function SuccessMessage({ children }: PropsWithChildren) {
  return (
    <div className="mb-6 rounded bg-green-100 px-4 py-3 text-green-700">
      {children}
    </div>
  )
}
