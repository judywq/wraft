<template>
  <Card class="mx-auto w-full sm:w-96 text-center">
    <CardHeader>
      <CardTitle class="text-2xl">Check your inbox</CardTitle>
      <CardDescription>
        If an account is associated with that address, you'll receive a link to reset your password
        shortly.
      </CardDescription>
    </CardHeader>

    <CardContent class="grid gap-3">
      <p class="text-sm text-muted-foreground">
        Didn’t get the email? Check your spam folder or try again.
      </p>
      <router-link :to="{ name: 'forgot-password' }" class="text-sm underline hover:no-underline"
        >Resend reset link</router-link
      >
    </CardContent>

    <CardFooter class="justify-center">
      <router-link :to="{ name: 'login' }">
        <Button class="w-full">Return to sign in</Button>
      </router-link>
    </CardFooter>
  </Card>
</template>

<script setup lang="ts">
/**
 * ResetLinkSentView
 * - Purely presentational.
 * - Keeps the copy short and neutral.
 */
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
</script>
