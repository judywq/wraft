<script setup lang="ts">
import { cn } from '@/lib/utils'
import { DropdownMenuItem as RadixDropdownMenuItem } from 'radix-vue'
import { computed } from 'vue'

const props = defineProps<{
  class?: string
  disabled?: boolean
}>()

const forwarded = computed(() => {
  return {
    ...props,
  }
})
</script>

<template>
  <RadixDropdownMenuItem
    v-bind="forwarded"
    :class="cn(
      'relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
      'hover:bg-white/10',
      props.class
    )"
  >
    <slot />
  </RadixDropdownMenuItem>
</template>
