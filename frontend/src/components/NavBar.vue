<script setup lang="ts">
import { ref, computed } from 'vue'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Sheet, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { Menu, User } from 'lucide-vue-next'

import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const router = useRouter()
const authStore = useAuthStore()
const isAuthenticated = computed(() => authStore.isAuthenticated)
const username = computed(() => authStore.user?.username || '')
const userInitials = computed(() => username.value.split(' ').map(name => name[0]).join(''))
const logout = () => {
  authStore.logout(router)
}
const menuItems = [
  {
    label: 'Evaluation',
    name: 'evaluation',
  },
]
const isSheetOpen = ref(false)
</script>

<template>
  <header
    class="sticky top-0 flex h-16 items-center gap-4 border-b bg-background/80 backdrop-blur-md px-4 md:px-6 z-50"
  >
    <nav
      class="hidden flex-col gap-6 text-lg font-medium md:flex md:flex-row md:items-center md:gap-5 md:text-sm lg:gap-6"
    >
      <router-link :to="{ name: 'home' }" class="items-center text-xl font-semibold"> WrAFT </router-link>
      <router-link
        v-for="item in menuItems"
        :key="item.label"
        :to="{ name: item.name }"
        class="text-muted-foreground transition-colors hover:text-foreground"
        :class="{ 'text-primary': $route.name === item.name }"
      >
        <span>{{ item.label }}</span>
      </router-link>
      <router-link v-if="isAuthenticated" :to="{ name: 'history' }" class="text-muted-foreground transition-colors hover:text-foreground">History</router-link>
    </nav>
    <Sheet v-model:open="isSheetOpen">
      <SheetTrigger as-child>
        <Button variant="outline" size="icon" class="shrink-0 md:hidden">
          <Menu class="h-5 w-5" />
          <span class="sr-only">Toggle navigation menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left">
        <SheetDescription className="hidden">Menu</SheetDescription>
        <SheetTitle><router-link
            :to="{ name: 'home' }"
            class="items-center text-2xl font-semibold"
            @click="isSheetOpen = false"
          >
            WrAFT
          </router-link></SheetTitle>
        <nav class="mt-6 grid gap-6 text-lg font-medium">
          <router-link v-for="item in menuItems" :key="item.label"
            :to="{ name: item.name }"
            class="text-muted-foreground hover:text-foreground"
            :class="{ 'text-primary': $route.name === item.name }"
            @click="isSheetOpen = false"
          >
            <span>{{ item.label }}</span>
          </router-link>
          <router-link v-if="isAuthenticated" :to="{ name: 'history' }" class="text-muted-foreground transition-colors hover:text-foreground">History</router-link>
        </nav>
      </SheetContent>
    </Sheet>
    <div class="ml-auto flex w-full items-center gap-4 md:ml-auto md:gap-2 lg:gap-4">
      <div class="ml-auto flex-1 sm:flex-initial"></div>
      <DropdownMenu>
        <DropdownMenuTrigger>
          <div class="user-profile" title="User Profile">
            <div class="profile-avatar">{{ userInitials }}</div>
          </div>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <template v-if="isAuthenticated">
            <DropdownMenuLabel>{{ username }}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem @click="router.push({ name: 'change-password' })">
              Change Password
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem @click="logout">Logout</DropdownMenuItem>
          </template>
          <template v-else>
            <DropdownMenuItem @click="router.push({ name: 'login' })">Login</DropdownMenuItem>
            <DropdownMenuItem @click="router.push({ name: 'signup' })">Sign up</DropdownMenuItem>
          </template>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  </header>
</template>

<style scoped>
.user-profile {
  cursor: pointer;
}


.profile-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #74b9ff, #0984e3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1rem;
}

.profile-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.profile-name {
  font-weight: 600;
  font-size: 0.9rem;
}

.profile-level {
  font-size: 0.75rem;
  opacity: 0.8;
}
</style>
