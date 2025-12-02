<script setup lang="ts">
import { cn } from '@/lib/utils'
import { DropdownMenuContent as RadixDropdownMenuContent } from 'radix-vue'
import { computed } from 'vue'

const props = defineProps<{
  class?: string
}>()

const forwarded = computed(() => {
  return {
    ...props,
  }
})
</script>

<template>
  <RadixDropdownMenuContent
    v-bind="forwarded"
    :class="
      cn(
        'z-50 min-w-[8rem] overflow-hidden rounded-md border p-1 text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
        'glass-card',
        props.class,
      )
    "
    :style="{
      '--card': '255 100% 100% / 0.7',
      '--card-shadow': '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
      '--card-blur': 'blur(12px)',
    }"
  >
    <slot />
  </RadixDropdownMenuContent>
</template>
