<template>
  <Card class="mx-auto w-full sm:w-96">
    <CardHeader>
      <CardTitle class="text-2xl">Update password</CardTitle>
      <CardDescription>Update your password for this account.</CardDescription>
    </CardHeader>

    <CardContent>
      <form class="grid gap-4" @submit="onSubmit">
        <FormField name="old_password" v-slot="{ componentField }">
          <FormItem>
            <FormLabel>Current password</FormLabel>
            <FormControl>
              <Input
                v-bind="componentField"
                type="password"
                autocomplete="current-password"
                :disabled="ui.busy || ui.success"
                required
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <FormField name="new_password1" v-slot="{ componentField }">
          <FormItem>
            <FormLabel>New password</FormLabel>
            <FormControl>
              <Input
                v-bind="componentField"
                type="password"
                autocomplete="new-password"
                minlength="8"
                :disabled="ui.busy || ui.success"
                required
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <FormField name="new_password2" v-slot="{ componentField }">
          <FormItem>
            <FormLabel>Confirm new password</FormLabel>
            <FormControl>
              <Input
                v-bind="componentField"
                type="password"
                autocomplete="new-password"
                minlength="8"
                :disabled="ui.busy || ui.success"
                required
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <Button type="submit" class="w-full" :disabled="ui.busy || ui.success">
          <template v-if="ui.busy">Saving…</template>
          <template v-else>Save changes</template>
        </Button>

        <p v-if="ui.error" class="text-sm text-destructive">{{ ui.error }}</p>
        <p v-if="ui.success" class="text-sm text-green-600">Password updated successfully.</p>
      </form>
    </CardContent>

    <CardFooter class="justify-center">
      <RouterLink class="text-sm underline hover:no-underline" :to="{ name: 'evaluate' }">
        Cancel
      </RouterLink>
    </CardFooter>
    
  </Card>
</template>

<script setup lang="ts">
/**
 * UpdatePasswordView
 * - Authenticated users can change their password
 * - Calls AuthService.changePassword(currentPassword, newPassword)
 * - Uses zod + vee-validate and a compact `ui` state object
 */
import { ref } from 'vue'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'

// UI components
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form'

// External
import { AuthService } from '@/services/authService'
import { updatePasswordFormSchema } from '@/lib/schema'

const { handleSubmit, setErrors } = useForm({
  validationSchema: toTypedSchema(updatePasswordFormSchema),
  initialValues: {
    old_password: '',
    new_password1: '',
    new_password2: '',
  },
})

const ui = ref<{ busy: boolean; success: boolean; error: string | null }>({
  busy: false,
  success: false,
  error: null,
})

const onSubmit = handleSubmit(async (payload) => {
  ui.value.busy = true
  ui.value.error = null
  try {
    await AuthService.changePassword(payload.old_password, payload.new_password1, payload.new_password2)
    ui.value.success = true
  } catch (e: any) {
    if (e?.fieldErrors) setErrors(e.fieldErrors)
    ui.value.error = e?.nonFieldError ?? 'Password change failed. Please try again.'
  } finally {
    ui.value.busy = false
  }
})
</script>
