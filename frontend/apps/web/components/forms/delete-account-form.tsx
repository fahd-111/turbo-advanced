'use client'

import { FormHeader } from '@frontend/ui/forms/form-header'
import { SubmitField } from '@frontend/ui/forms/submit-field'
import { TextField } from '@frontend/ui/forms/text-field'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import type {
  DeleteAccountFormSchema,
  deleteAccountAction
} from '@/actions/delete-account-action'
import { signOut } from '@/lib/auth-client'
import { deleteAccountFormSchema } from '@/lib/validation'

export function DeleteAccountForm({
  onSubmitHandler,
  username
}: {
  onSubmitHandler: typeof deleteAccountAction
  username: string
}) {
  const { formState, handleSubmit, register, reset } =
    useForm<DeleteAccountFormSchema>({
      resolver: zodResolver(deleteAccountFormSchema),
      defaultValues: { usernameCurrent: username }
    })

  return (
    <>
      <FormHeader
        title="Delete your account"
        description="After this action all data will be lost"
      />

      <form
        method="post"
        onSubmit={handleSubmit(async (data) => {
          const res = await onSubmitHandler(data)

          if (res) {
            reset()
            await signOut().catch(() => window.location.assign('/login'))
          }
        })}
      >
        <TextField
          type="text"
          register={register('username')}
          label="Username"
          formState={formState}
        />

        <SubmitField>Delete account</SubmitField>
      </form>
    </>
  )
}
