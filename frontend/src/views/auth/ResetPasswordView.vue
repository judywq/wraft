<template>
  <Card class="w-full mx-auto sm:w-96">
    <CardHeader>
      <CardTitle class="text-2xl">Reset Password</CardTitle>
      <CardDescription>Enter your new password below</CardDescription>
    </CardHeader>
    <CardContent>
      <form @submit="handleSubmit" class="grid gap-4">
        <FormField
          v-slot="{ componentField }"
          name="new_password1"
        >
          <FormItem>
            <FormLabel>New Password</FormLabel>
            <FormControl>
              <Input
                v-bind="componentField"
                type="password"
                placeholder="Enter your new password"
                :disabled="isSubmitting || success"
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <FormField
          v-slot="{ componentField }"
          name="new_password2"
        >
          <FormItem>
            <FormLabel>Confirm Password</FormLabel>
            <FormControl>
              <Input
                v-bind="componentField"
                type="password"
                placeholder="Confirm your new password"
                :disabled="isSubmitting || success"
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <div v-if="generalError" class="text-destructive text-sm text-center">
          {{ generalError }}
        </div>

        <Button
          type="submit"
          class="w-full"
          :disabled="isSubmitting || !form.meta.value.valid || success"
        >
          {{ isSubmitting ? 'Resetting...' : 'Reset Password' }}
        </Button>

        <p v-if="success" class="text-success-foreground text-sm text-center">
          Password reset successful. Redirecting to
          <router-link :to="{ name: 'login' }" class="underline">login</router-link>
          ...
        </p>
      </form>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from '@/components/ui/toast/use-toast'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { AuthService } from '@/services/authService'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import * as z from 'zod'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { resetPasswordFormSchema } from '@/lib/validations'

const { toast } = useToast()
const router = useRouter()
const route = useRoute()
const isSubmitting = ref(false)
const generalError = ref<string | null>(null)
const success = ref(false)

const form = useForm({
  validationSchema: toTypedSchema(resetPasswordFormSchema),
  initialValues: {
    new_password1: '',
    new_password2: '',
  },
})

const handleSubmit = form.handleSubmit(async (values) => {
  isSubmitting.value = true
  generalError.value = null

  try {
    await AuthService.passwordResetConfirm(
      route.params.uid as string,
      route.params.token as string,
      values.new_password1,
      values.new_password2,
    )
    success.value = true
    // Navigate to the login page after 3 seconds
    setTimeout(() => {
      router.push({ name: 'login' })
    }, 3000)
  } catch (err: any) {
    if (err.fieldErrors) {
      form.setErrors(err.fieldErrors)
    }
    if (err.nonFieldError) {
      generalError.value = err.nonFieldError
    }
    toast({
      description: err.nonFieldError || 'An error occurred, please try again later.',
        variant: 'destructive',
      })
  } finally {
    isSubmitting.value = false
  }
})
</script>
