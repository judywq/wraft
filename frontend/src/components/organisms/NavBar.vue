<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import { Menu } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

// Router and route
const router = useRouter()
const route = useRoute()

// Auth store
const authStore = useAuthStore()
const isAuthenticated = computed(() => authStore.isAuthenticated)
const username = computed(() => authStore.user?.username || '')
const userInitials = computed(() => {
  if (!username.value) return 'U'
  return (
    username.value
      .split(' ')
      .map((name) => name[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'U'
  )
})

// Navigation menu items
const menuItems = [
  {
    label: 'Evaluate',
    name: 'evaluate',
    icon: '📝',
  },
]

// Mobile menu state
const isSheetOpen = ref(false)

// Methods
const logout = () => {
  authStore.logout(router)
}

const handleNavigation = (routeName: string) => {
  isSheetOpen.value = false
  router.push({ name: routeName })
}

const isActiveRoute = (routeName: string) => {
  return route.name === routeName
}
</script>

<template>
  <header class="navbar-header">
    <!-- Desktop Navigation -->
    <nav class="navbar-desktop">
      <router-link :to="{ name: 'home' }" class="navbar-brand"> WrAFT </router-link>

      <div class="navbar-links">
        <router-link
          v-for="item in menuItems"
          :key="item.name"
          :to="{ name: item.name }"
          class="navbar-link"
          :class="{ 'navbar-link-active': isActiveRoute(item.name) }"
        >
          <span class="navbar-link-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>

        <router-link
          v-if="isAuthenticated"
          :to="{ name: 'history' }"
          class="navbar-link"
          :class="{ 'navbar-link-active': isActiveRoute('history') }"
        >
          <span class="navbar-link-icon">📚</span>
          <span>History</span>
        </router-link>
      </div>
    </nav>

    <!-- Mobile Menu Toggle -->
    <Sheet v-model:open="isSheetOpen">
      <SheetTrigger as-child>
        <Button variant="outline" size="icon" class="navbar-mobile-toggle">
          <Menu class="h-5 w-5" />
          <span class="sr-only">Toggle navigation menu</span>
        </Button>
      </SheetTrigger>

      <SheetContent side="left" class="navbar-mobile-content">
        <SheetDescription class="sr-only">Navigation Menu</SheetDescription>
        <SheetTitle class="navbar-mobile-title">
          <router-link
            :to="{ name: 'home' }"
            class="navbar-brand-mobile"
            @click="isSheetOpen = false"
          >
            WrAFT
          </router-link>
        </SheetTitle>

        <nav class="navbar-mobile-nav">
          <router-link
            v-for="item in menuItems"
            :key="item.name"
            :to="{ name: item.name }"
            class="navbar-mobile-link"
            :class="{ 'navbar-mobile-link-active': isActiveRoute(item.name) }"
            @click="handleNavigation(item.name)"
          >
            <span class="navbar-link-icon">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </router-link>

          <router-link
            v-if="isAuthenticated"
            :to="{ name: 'history' }"
            class="navbar-mobile-link"
            :class="{ 'navbar-mobile-link-active': isActiveRoute('history') }"
            @click="handleNavigation('history')"
          >
            <span class="navbar-link-icon">📚</span>
            <span>History</span>
          </router-link>
        </nav>
      </SheetContent>
    </Sheet>

    <!-- User Profile Dropdown -->
    <div class="navbar-user-section">
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <button class="navbar-user-trigger" :title="username || 'User Profile'">
            <div class="profile-avatar">
              {{ userInitials }}
            </div>
          </button>
        </DropdownMenuTrigger>

        <DropdownMenuContent align="end" class="navbar-dropdown">
          <template v-if="isAuthenticated">
            <DropdownMenuLabel class="navbar-dropdown-label">
              {{ username }}
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem @click="router.push({ name: 'change-password' })">
              🔐 Change Password
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem @click="logout" class="text-destructive">
              🚪 Logout
            </DropdownMenuItem>
          </template>
          <template v-else>
            <DropdownMenuItem @click="router.push({ name: 'login' })"> 🔑 Login </DropdownMenuItem>
            <DropdownMenuItem @click="router.push({ name: 'signup' })">
              ✨ Sign up
            </DropdownMenuItem>
          </template>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  </header>
</template>

<style scoped>
/* Header Container */
.navbar-header {
  position: sticky;
  top: 0;
  display: flex;
  height: 4rem;
  align-items: center;
  gap: 1rem;
  border-bottom: 1px solid hsl(var(--border));
  background: hsl(var(--background) / 0.8);
  backdrop-filter: blur(12px);
  padding: 0 1rem;
  z-index: 50;
}

@media (min-width: 768px) {
  .navbar-header {
    padding: 0 1.5rem;
  }
}

/* Desktop Navigation */
.navbar-desktop {
  display: none;
  flex: 1;
  flex-direction: column;
  gap: 1.5rem;
  font-size: 1.125rem;
  font-weight: 500;
}

@media (min-width: 768px) {
  .navbar-desktop {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 1.25rem;
    font-size: 0.875rem;
  }
}

@media (min-width: 1024px) {
  .navbar-desktop {
    gap: 1.5rem;
  }
}

/* Brand Logo */
.navbar-brand {
  display: flex;
  align-items: center;
  font-size: 1.25rem;
  font-weight: 600;
  color: hsl(var(--foreground));
  text-decoration: none;
  transition: opacity 0.2s;
}

.navbar-brand:hover {
  opacity: 0.8;
}

.navbar-brand-mobile {
  font-size: 1.5rem;
  font-weight: 600;
  color: hsl(var(--foreground));
  text-decoration: none;
}

/* Navigation Links */
.navbar-links {
  display: flex;
  gap: 1.25rem;
  align-items: center;
}

.navbar-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: hsl(var(--muted-foreground));
  text-decoration: none;
  transition: color 0.2s;
  font-size: 0.875rem;
}

.navbar-link:hover {
  color: hsl(var(--foreground));
}

.navbar-link-active {
  color: hsl(var(--foreground));
  font-weight: 500;
}

.navbar-link-icon {
  font-size: 1rem;
  line-height: 1;
}

/* Mobile Menu */
.navbar-mobile-toggle {
  flex-shrink: 0;
}

@media (min-width: 768px) {
  .navbar-mobile-toggle {
    display: none;
  }
}

.navbar-mobile-content {
  width: 18rem;
}

.navbar-mobile-title {
  margin-bottom: 1.5rem;
}

.navbar-mobile-nav {
  display: grid;
  gap: 1.5rem;
  font-size: 1.125rem;
  font-weight: 500;
}

.navbar-mobile-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: hsl(var(--muted-foreground));
  text-decoration: none;
  transition: color 0.2s;
  padding: 0.5rem 0;
}

.navbar-mobile-link:hover {
  color: hsl(var(--foreground));
}

.navbar-mobile-link-active {
  color: hsl(var(--primary));
  font-weight: 600;
}

/* User Section */
.navbar-user-section {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 1rem;
}

/* User Profile Trigger */
.navbar-user-trigger {
  cursor: pointer;
  border: none;
  background: transparent;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s;
}

.navbar-user-trigger:hover {
  transform: scale(1.05);
}

.navbar-user-trigger:active {
  transform: scale(0.95);
}

/* Profile Avatar */
.profile-avatar {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  box-shadow: 0 2px 8px rgba(116, 185, 255, 0.3);
  transition: box-shadow 0.2s;
}

.profile-avatar:hover {
  box-shadow: 0 4px 12px rgba(116, 185, 255, 0.4);
}

/* Dropdown Menu */
.navbar-dropdown {
  min-width: 12rem;
}

.navbar-dropdown-label {
  font-weight: 600;
  padding: 0.5rem 0.75rem;
}

/* Screen Reader Only */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
</style>
