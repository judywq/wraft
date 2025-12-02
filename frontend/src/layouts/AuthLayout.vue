<script setup lang="ts">
// Layout for public auth pages (login, register, etc.)
import { watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

// Send logged-in users to the app
watchEffect(() => {
  if (auth.isAuthenticated) {
    router.push({ name: 'evaluate' })
  }
})
</script>

<template>
  <div class="min-h-screen bg-background flex flex-col">
    <nav class="w-full py-4 border-b">
      <div class="container mx-auto px-4">
        <router-link :to="{ name: 'home' }" class="flex items-center justify-center">
          <span class="text-2xl font-bold">WrAFT</span>
        </router-link>
      </div>
    </nav>

    <main class="flex-grow flex items-start justify-center px-4 py-8">
      <div class="w-full">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in" appear>
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>
