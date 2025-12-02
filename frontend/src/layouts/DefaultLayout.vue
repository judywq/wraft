<script setup lang="ts">
// Main layout for protected routes
import { watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import NavBar from '@/components/organisms/NavBar.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

// Protect routes that require authentication
watchEffect(() => {
  const currentRoute = router.currentRoute.value
  const needsAuth = currentRoute.meta.requiresAuth === true

  if (needsAuth && !auth.isAuthenticated) {
    router.push({ name: 'login' })
  }
})
</script>

<template>
  <div class="min-h-screen bg-background flex flex-col">
    <NavBar />
    <main class="flex-grow container mx-auto px-4 py-8">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in" appear>
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.1s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
