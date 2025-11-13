<template>
  <Card class="mx-auto w-full sm:w-96">
    <CardHeader>
      <CardTitle class="text-2xl">Verify your email</CardTitle>
      <CardDescription>Enter the verification code we sent to your email.</CardDescription>
    </CardHeader>

    <CardContent>
      <form class="grid gap-4" @submit="onSubmit">
        <FormField name="verificationCode" v-slot="{ componentField }">
          <FormItem>
            <FormLabel>Verification code</FormLabel>
            <FormControl>
              <Input
                v-bind="componentField"
                type="text"
                inputmode="numeric"
                autocomplete="one-time-code"
                placeholder="6-digit code"
                :disabled="ui.busy || ui.verified"
                required
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <Button type="submit" class="w-full" :disabled="ui.busy || ui.verified">
          <template v-if="ui.busy">Checking…</template>
          <template v-else>Verify</template>
        </Button>

        <p v-if="ui.error" class="text-sm text-destructive">{{ ui.error }}</p>
        <p v-if="ui.verified" class="text-sm text-green-600">Email verified. Thank you!</p>
      </form>
    </CardContent>

    <CardFooter class="justify-between gap-2">
      <RouterLink class="text-sm underline hover:no-underline" :to="{ name: 'login' }">
        Back to sign in
      </RouterLink>
      <RouterLink class="text-sm underline hover:no-underline" :to="{ name: 'signup' }">
        Create account
      </RouterLink>
    </CardFooter>
  </Card>
</template>

<script setup lang="ts">
/**
 * EmailVerificationView
 * - Verifies a code, typically received by email
 * - Calls AuthService.verifyEmail(code)
 * - Clean UI with single `ui` object for state
 */
import { ref } from 'vue'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'

// UI components
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form'
import { RouterLink } from 'vue-router'

// External API
import { AuthService } from '@/services/authService'
import { verifyEmailFormSchema } from '@/lib/schema'

const { handleSubmit, setErrors } = useForm({
  validationSchema: toTypedSchema(verifyEmailFormSchema),
  initialValues: { verificationCode: '' },
})

const ui = ref<{ busy: boolean; verified: boolean; error: string | null }>({
  busy: false,
  verified: false,
  error: null,
})

const onSubmit = handleSubmit(async (values) => {
  ui.value.busy = true
  ui.value.error = null
  try {
    await AuthService.verifyEmail(values.verificationCode)
    ui.value.verified = true
  } catch (e: any) {
    if (e?.fieldErrors) setErrors(e.fieldErrors)
    ui.value.error = e?.nonFieldError ?? 'Verification failed. Please try again.'
  } finally {
    ui.value.busy = false
  }
})
</script>
