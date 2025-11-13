<template>
  <div class="view-content">
    <!-- Loading state for corrected text -->
    <div v-if="!hasCorrectedText" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading corrected essay...</p>
    </div>

    <div v-else class="content-layout">
      <div class="text-column">
        <div class="text-container" id="corrected-text-container">
          <div
            v-for="(paragraph, index) in paragraphs"
            :key="index"
            class="text-paragraph"
          >
            {{ paragraph }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { EssayEvaluationData } from '@/models/writing'
import { PARAGRAPH_DELIMITER } from '@/lib/utils'

const props = defineProps<{
  evaluationData: EssayEvaluationData
}>()

const paragraphs = computed(() => {
  // Return empty array if corrected text is not available yet
  return props.evaluationData.essay_text_corrected?.split(PARAGRAPH_DELIMITER) ?? []
})

// Computed property to check if corrected text exists
const hasCorrectedText = computed(() => {
  return !!props.evaluationData?.essay_text_corrected
})
</script>

<style scoped>
.view-content {
  margin-top: 20px;
}

.content-layout {
  position: relative;
  width: 100%;
}

.text-column {
  width: 55% !important;
  margin: 0 auto !important;
}

.text-container {
  color: var(--primary-color);
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  line-height: 1.8;
}

.text-paragraph {
  position: relative;
  padding: 10px 0;
}

@media (max-width: 1024px) {
  .text-column {
    width: 70% !important;
  }
}

@media (max-width: 768px) {
  .text-column {
    width: 90% !important;
  }
}

/* Add styles for the new loading container */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
