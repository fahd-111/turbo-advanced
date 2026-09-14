'use client'

import { submitAuthentication } from '@/lib/auth-client'
import { loginFormSchema } from '@/lib/validation'
import { FormFooter } from '@frontend/ui/forms/form-footer'
import { FormHeader } from '@frontend/ui/forms/form-header'
import { SubmitField } from '@frontend/ui/forms/submit-field'
import { TextField } from '@frontend/ui/forms/text-field'
import { ErrorMessage } from '@frontend/ui/messages/error-message'
import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import type { z } from 'zod'

type LoginFormSchema = z.infer<typeof loginFormSchema>

export function LoginForm() {
  const [error, setError] = useState('')

  const { register, handleSubmit, formState } = useForm<LoginFormSchema>({
    resolver: zodResolver(loginFormSchema)
  })

  const onSubmitHandler = handleSubmit(async (data) => {
    setError('')
    try {
      const response = await submitAuthentication('login', data)
      if (!response.ok) {
        setError(
          response.status === 400
            ? 'Invalid username or password.'
            : 'Unable to sign in. Please try again.'
        )
        return
      }
      window.location.assign('/')
    } catch {
      setError('Unable to sign in. Please try again.')
    }
  })

  return (
    <>
      <FormHeader
        title="Welcome back to Turbo"
        description="Get an access to internal application"
      />

      {error && <ErrorMessage>{error}</ErrorMessage>}

      <form method="post" onSubmit={onSubmitHandler}>
        <TextField
          type="text"
          register={register('username')}
          formState={formState}
          label="Username"
          placeholder="Email address or username"
        />

        <TextField
          type="password"
          register={register('password', { required: true })}
          formState={formState}
          label="Password"
          placeholder="Enter your password"
        />

        <SubmitField isLoading={formState.isSubmitting}>Sign in</SubmitField>
      </form>

      <FormFooter
        cta="Don't have an account?"
        link="/register"
        title="Sign up"
      />
    </>
  )
}
