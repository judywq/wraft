<template>
  <Card class="mx-auto w-full sm:w-96">
    <CardHeader>
      <CardTitle class="text-2xl">Forgot Password</CardTitle>
      <CardDescription>
        Tell us your email and we'll send a reset link.
      </CardDescription>
    </CardHeader>

    <CardContent>
      <!-- Using a simple form with validation state from vee-validate -->
      <form class="grid gap-4" @submit="onSubmit">
        <FormField name="email" v-slot="{ componentField }">
          <FormItem>
            <FormLabel>Email</FormLabel>
            <FormControl>
              <Input
                v-bind="componentField"
                type="email"
                inputmode="email"
                autocomplete="email"
                placeholder="name@example.com"
                :disabled="ui.busy || ui.sent"
                required
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <Button type="submit" :disabled="ui.busy || ui.sent" class="w-full">
          <template v-if="ui.busy">Sending…</template>
          <template v-else>Send reset link</template>
        </Button>

        <p v-if="ui.generalErr" class="text-sm text-destructive">{{ ui.generalErr }}</p>
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'

// UI components (shadcn-vue style)
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form'

// External API (keep method names intact)
import { AuthService } from '@/services/authService'
import { requestPasswordResetFormSchema } from '@/lib/schema'

const { handleSubmit, setErrors } = useForm({
  validationSchema: toTypedSchema(requestPasswordResetFormSchema),
  initialValues: { email: '' },
})

// Centralized UI state to avoid scattering many refs
const ui = ref<{ busy: boolean; sent: boolean; generalErr: string | null }>({
  busy: false,
  sent: false,
  generalErr: null,
})

const router = useRouter()

const onSubmit = handleSubmit(async (formValues) => {
  ui.value.busy = true
  ui.value.generalErr = null
  try {
    await AuthService.passwordReset(formValues.email)
    ui.value.sent = true
    router.push({ name: 'password-reset-sent' })
  } catch (e: any) {
    // If your backend returns fieldErrors/nonFieldError, handle them here
    if (e?.fieldErrors) setErrors(e.fieldErrors)
    ui.value.generalErr = e?.nonFieldError ?? 'Unable to send reset email. Please try again.'
  } finally {
    ui.value.busy = false
  }
})
</script>
