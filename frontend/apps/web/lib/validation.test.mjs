import assert from 'node:assert/strict'
import test from 'node:test'
import { changePasswordFormSchema, registerFormSchema } from './validation.ts'

test('registration and password-change validation survive dependency upgrades', () => {
  const registration = {
    username: 'test-user',
    password: 'strong-password',
    passwordRetype: 'strong-password'
  }
  assert.equal(registerFormSchema.safeParse(registration).success, true)
  assert.equal(
    registerFormSchema.safeParse({
      ...registration,
      passwordRetype: 'different'
    }).success,
    false
  )
  const passwordChange = {
    password: 'old-password',
    passwordNew: 'new-password',
    passwordRetype: 'new-password'
  }
  assert.equal(changePasswordFormSchema.safeParse(passwordChange).success, true)
  assert.equal(
    changePasswordFormSchema.safeParse({
      ...passwordChange,
      passwordNew: 'old-password',
      passwordRetype: 'old-password'
    }).success,
    false
  )
})
