<script setup lang="ts">
/**
 * BaseLayout Component
 *
 * Main layout wrapper for authenticated pages.
 * Features:
 * - Full navigation bar with user menu
 * - Authentication guard (redirects unauthenticated users)
 * - Fade transition animations for route changes
 *
 * Used by: Evaluate, Results, Profile, Settings, etc.
 */

import NavBar from '@/components/organisms/NavBar.vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import { onMounted } from 'vue';

const authStore = useAuthStore();
const router = useRouter();

/**
 * Authentication Guard
 * Redirects unauthenticated users to login page if route requires authentication
 * Only checks routes that have `meta.requiresAuth` set to true
 */
onMounted(() => {
  if (!authStore.isAuthenticated && router.currentRoute.value.meta.requiresAuth) {
    router.push({ name: 'login' });
  }
});
</script>

<template>
  <div class="min-h-screen bg-background flex flex-col">
    <!-- Full Navigation Bar -->
    <!-- Includes user menu, navigation links, and authentication controls -->
    <NavBar />

    <!-- Main Content Area -->
    <!-- Container with responsive padding and max-width constraints -->
    <main class="flex-grow container mx-auto px-4 py-8">
      <!-- Router View with Fade Transition -->
      <!-- Provides smooth transitions between authenticated pages -->
      <router-view v-slot="{ Component }">
        <transition
          name="fade"
          mode="out-in"
          appear
        >
          <component :is="Component" />
        </transition>
      </router-view>
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
