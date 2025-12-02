<script setup lang="ts">
import { cn } from '@/lib/utils'
import { DropdownMenuLabel as RadixDropdownMenuLabel } from 'radix-vue'
import { computed } from 'vue'

const props = defineProps<{
  class?: string
  inset?: boolean
}>()

const forwarded = computed(() => {
  return {
    ...props,
  }
})
</script>

<template>
  <RadixDropdownMenuLabel
    v-bind="forwarded"
    :class="
      cn('px-2 py-1.5 text-sm font-semibold', 'text-white/90', props.inset && 'pl-8', props.class)
    "
  >
    <slot />
  </RadixDropdownMenuLabel>
</template>
