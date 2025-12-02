<template>
  <div class="container">
    <!-- View toggle buttons -->
    <div class="view-toggle-container">
      <button
        class="view-toggle-btn"
        :class="{ active: currentView === 'surface' }"
        @click="currentView = 'surface'"
      >
        Surface Level Feedback
      </button>
      <button
        class="view-toggle-btn"
        :class="{ active: currentView === 'deep' }"
        @click="currentView = 'deep'"
      >
        Deep Level Feedback
      </button>
      <button
        class="view-toggle-btn"
        :class="{ active: currentView === 'corrected' }"
        @click="currentView = 'corrected'"
      >
        Corrected Essay
      </button>
    </div>

    <!-- View subtitle - changes based on the selected view -->
    <h2 id="view-subtitle" class="subtitle">{{ viewSubtitle }}</h2>

    <div class="score-container">
      <div class="score-box">
        <h3>Score</h3>
        <div v-if="evaluationData?.score != null" class="score-value">
          {{ evaluationData.score }}
        </div>
        <div v-else class="loading-container small-loading">
          <div class="loading-spinner small-spinner"></div>
        </div>
      </div>
    </div>

    <!-- Essay prompt section - visible in all views -->
    <div class="prompt-container">
      <div class="prompt-box">
        <h3>Essay Prompt</h3>
        <div id="essay-prompt">{{ evaluationData?.essay_prompt }}</div>
      </div>
    </div>

    <!-- Error state -->
    <div v-if="error" class="error-container">
      <p class="error-message">{{ error }}</p>
    </div>

    <!-- Content when data is loaded -->
    <template v-else>
      <!-- Surface Level Feedback View -->
      <SurfaceView
        v-if="currentView === 'surface' && evaluationData"
        :evaluation-data="evaluationData"
        :status="evaluationRequest?.status"
        :current-view="surfaceCurrentView"
        @update-view="surfaceCurrentView = $event"
      />

      <!-- Deep Level Feedback View -->
      <DeepView v-if="currentView === 'deep' && evaluationData" :evaluation-data="evaluationData" />

      <!-- Corrected Essay View -->
      <CorrectedView
        v-if="currentView === 'corrected' && evaluationData"
        :evaluation-data="evaluationData"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import SurfaceView from '@/components/assessment/SurfaceView.vue'
import DeepView from '@/components/assessment/DeepView.vue'
import CorrectedView from '@/components/assessment/CorrectedView.vue'
import type { EssayRequest } from '@/models/writing'
import { EssayService } from '@/services/writingService'

const route = useRoute()
const currentView = ref('surface')
const surfaceCurrentView = ref('track-changes')
const evaluationRequest = ref<EssayRequest | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)
const pollingInterval = ref<ReturnType<typeof setInterval> | null>(null)

const evaluationData = computed(() => {
  if (!evaluationRequest.value?.evaluation) {
    return null
  }
  return evaluationRequest.value.evaluation
})

const viewSubtitle = computed(() => {
  switch (currentView.value) {
    case 'surface':
      return 'Surface Level Feedback'
    case 'deep':
      return 'Deep Level Feedback'
    case 'corrected':
      return 'Corrected Essay'
    default:
      return ''
  }
})

const startPolling = () => {
  if (pollingInterval.value) return // already polling
  pollingInterval.value = setInterval(async () => {
    await fetchEvaluationRequest(false)
    const status = evaluationRequest.value?.status
    if (status === 'COMPLETED' || status === 'FAILED') {
      stopPolling()
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
}

const fetchEvaluationRequest = async (showLoading = true) => {
  try {
    if (showLoading) isLoading.value = true
    error.value = null
    const id = route.params.id as string
    const response = await EssayService.getEssayEvaluation(parseInt(id))
    evaluationRequest.value = response

    // Check if the evaluation itself failed after successful API call
    if (evaluationRequest.value?.status === 'FAILED') {
      error.value =
        evaluationRequest.value?.error ||
        'The evaluation process failed. Please try again or contact support.'
      stopPolling() // Ensure polling stops if it was running
    }
  } catch (err) {
    error.value = 'Failed to load evaluation data. Please try again later.'
    console.error('Error fetching evaluation data:', err)
    stopPolling()
  } finally {
    if (showLoading) isLoading.value = false
  }
}

onMounted(async () => {
  await fetchEvaluationRequest()
  const status = evaluationRequest.value?.status
  if (status === 'PENDING' || status === 'PROCESSING') {
    isLoading.value = true // keep loading spinner
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.container {
  max-width: 100%;
  margin: 0 auto;
  padding: 20px;
  position: relative;
}

.subtitle {
  color: white;
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 20px;
  text-align: center;
}

/* View toggle styling */
.view-toggle-container {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.view-toggle-btn {
  background-color: #f1f5f9;
  color: #64748b;
  border: 1px solid #cbd5e1;
  padding: 10px 20px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  margin: 0 5px;
}

.view-toggle-btn:first-child {
  border-radius: 4px 0 0 4px;
}

.view-toggle-btn:last-child {
  border-radius: 0 4px 4px 0;
}

.view-toggle-btn.active {
  background-color: #2c5282;
  color: white;
  border-color: #2c5282;
}

.view-toggle-btn:hover:not(.active) {
  background-color: #e2e8f0;
}

/* Essay prompt styling */
.prompt-container {
  width: 55%;
  margin-left: auto;
  margin-right: auto;
  margin-bottom: 30px;
}

.prompt-box {
  color: var(--primary-color);
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.prompt-box h3 {
  margin-top: 0;
  color: var(--primary-color);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 10px;
}

/* Score display styling */
.score-container {
  position: fixed;
  top: 260px;
  right: 5%;
  width: 130px;
  z-index: 100;
}

.score-box {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 15px;
  text-align: center;
}

.score-box h3 {
  margin-top: 0;
  color: var(--primary-color);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 1px;
}

.score-value {
  font-size: 28px;
  font-weight: bold;
  color: var(--primary-color);
  margin: 10px 0;
}

/* Responsive styles */
@media (max-width: 1200px) {
  .score-container {
    position: absolute;
    top: 20px;
    right: 5%;
  }
}

@media (max-width: 1024px) {
  .prompt-container {
    width: 70% !important;
  }

  .score-container {
    position: static;
    margin: 0 auto 20px auto;
  }
}

@media (max-width: 768px) {
  .prompt-container {
    width: 90% !important;
  }

  .view-toggle-btn {
    padding: 8px 10px;
    font-size: 13px;
  }
}

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
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.error-container {
  display: flex;
  justify-content: center;
  padding: 40px;
}

.error-message {
  color: #e74c3c;
  font-size: 16px;
  text-align: center;
}

/* Add styles for the smaller loading container in the score box */
.small-loading {
  padding: 10px 0; /* Adjusted padding */
  display: flex;
  justify-content: center;
  align-items: center;
}

.small-spinner {
  width: 24px; /* Smaller spinner */
  height: 24px;
  border-width: 3px; /* Thinner border */
  margin-bottom: 0; /* Remove margin if centered inline */
}
</style>
