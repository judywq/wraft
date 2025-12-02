<template>
  <Card class="mx-auto w-full sm:w-96">
    <CardHeader>
      <CardTitle class="text-2xl">Set a new password</CardTitle>
      <CardDescription>
        Your new password should be hard to guess but easy for you to remember.
      </CardDescription>
    </CardHeader>

    <CardContent>
      <form class="grid gap-4" @submit="onSubmit">
        <FormField name="new_password1" v-slot="{ componentField }">
          <FormItem>
            <FormLabel>New password</FormLabel>
            <FormControl>
              <Input
                v-bind="componentField"
                type="password"
                autocomplete="new-password"
                :disabled="ui.busy || ui.done"
                minlength="8"
                required
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <FormField name="new_password2" v-slot="{ componentField }">
          <FormItem>
            <FormLabel>Confirm password</FormLabel>
            <FormControl>
              <Input
                v-bind="componentField"
                type="password"
                autocomplete="new-password"
                :disabled="ui.busy || ui.done"
                minlength="8"
                required
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <Button type="submit" class="w-full" :disabled="ui.busy || ui.done">
          <template v-if="ui.busy">Updating…</template>
          <template v-else>Update password</template>
        </Button>

        <p v-if="ui.generalErr" class="text-sm text-destructive">{{ ui.generalErr }}</p>
        <p v-if="ui.done" class="text-sm text-green-600">Password updated. You can now sign in.</p>
      </form>
    </CardContent>

    <CardFooter class="justify-center">
      <RouterLink :to="{ name: 'login' }" class="text-sm underline hover:no-underline">
        Back to sign in
      </RouterLink>
    </CardFooter>
  </Card>
</template>

<script setup lang="ts">
/**
 * SetNewPasswordView
 * - Consumes a password reset token from the route query/params
 * - Calls AuthService.resetPassword(token, newPassword)
 * - Uses a compact `ui` state object and zod-based validation
 */
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'

// UI components
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form'

// External API (names must remain intact)
import { AuthService } from '@/services/authService'
import { setNewPasswordFormSchema } from '@/lib/schema'

// Grab token from route. Adjust param/source according to your app (query vs params).
const route = useRoute()
const token = computed(() => (route.query.token ?? route.params.token ?? '') as string)

// Form schema
const { handleSubmit, setErrors } = useForm({
  validationSchema: toTypedSchema(setNewPasswordFormSchema),
  initialValues: { new_password1: '', new_password2: '' },
})

const ui = ref<{ busy: boolean; done: boolean; generalErr: string | null }>({
  busy: false,
  done: false,
  generalErr: null,
})

const router = useRouter()

const onSubmit = handleSubmit(async (values) => {
  ui.value.busy = true
  ui.value.generalErr = null
  try {
    await AuthService.passwordResetConfirm(
      route.params.uid as string,
      route.params.token as string,
      values.new_password1,
      values.new_password2,
    )
    ui.value.done = true
  } catch (e: any) {
    if (e?.fieldErrors) setErrors(e.fieldErrors)
    ui.value.generalErr = e?.nonFieldError ?? 'Could not reset password. Please retry.'
  } finally {
    ui.value.busy = false
  }
})
</script>
