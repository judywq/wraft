<script setup lang="ts">
import { cn } from '@/lib/utils'
import { DropdownMenuSeparator as RadixDropdownMenuSeparator } from 'radix-vue'
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
  <RadixDropdownMenuSeparator
    v-bind="forwarded"
    :class="cn('-mx-1 my-1 h-px', 'bg-white/10', props.class)"
  />
</template>
