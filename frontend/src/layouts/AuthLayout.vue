<script setup lang="ts">
/**
 * AuthLayout Component
 *
 * Layout wrapper for authentication-related pages (login, signup, etc.).
 * Features:
 * - Simplified navigation (logo only, no full NavBar)
 * - Redirects authenticated users away from auth pages
 * - Fade transition animations for route changes
 *
 * Used by: Login, Signup, Forgot Password, Verify Email, etc.
 */

import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import { onMounted } from 'vue';

const authStore = useAuthStore();
const router = useRouter();

/**
 * Redirect authenticated users away from auth pages
 * If user is already logged in, redirect to the evaluate page
 * This prevents authenticated users from accessing login/signup pages
 */
onMounted(() => {
  if (authStore.isAuthenticated) {
    router.push({ name: 'evaluate' });
  }
});
</script>

<template>
  <div class="min-h-screen bg-background flex flex-col">
    <!-- Simplified Navigation Bar -->
    <!-- Only shows logo/brand, no user menu or navigation links -->
    <nav class="w-full py-4 border-b">
      <div class="container mx-auto px-4">
        <router-link :to="{ name: 'home' }" class="flex items-center justify-center">
          <span class="text-2xl font-bold">WrAFT</span>
        </router-link>
      </div>
    </nav>

    <!-- Main Content Area -->
    <!-- Centered layout for auth forms -->
    <main class="flex-grow flex items-start justify-center px-4 py-8">
      <div class="w-full">
        <!-- Router View with Fade Transition -->
        <!-- Provides smooth transitions between auth pages -->
        <router-view v-slot="{ Component }">
          <transition
            name="fade"
            mode="out-in"
            appear
          >
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
