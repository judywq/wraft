<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, FileText } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { EssayService } from '@/services/writingService'
import { columns } from '@/components/results/columns'
import DataTable from '@/components/results/DataTable.vue'
import type { EssayEvaluationDataBrief } from '@/models/writing'
import { useWritingPolling } from '@/composables/useWritingPolling'

// Router
const router = useRouter()

// Constants
const ITEMS_TO_RETRIEVE = 1000

// State
const data = ref<EssayEvaluationDataBrief[]>([])
const totalItems = ref(0)
const currentPage = ref(1)
const selectedRecord = ref<EssayEvaluationDataBrief | null>(null)

// Composables
const { startPolling } = useWritingPolling()

// Methods
const startHistoryPolling = () => {
  startPolling({
    page: currentPage.value,
    pageSize: ITEMS_TO_RETRIEVE,
    onData: (results) => {
      data.value = results

      // Update dialog content if open
      if (selectedRecord.value) {
        const updatedRecord = results.find((r) => r.id === selectedRecord.value?.id)
        if (updatedRecord) {
          selectedRecord.value = updatedRecord
        }
      }
    },
  })
}

async function loadData(page: number) {
  try {
    const response = await EssayService.getEssayHistory(page, ITEMS_TO_RETRIEVE)
    data.value = response.results
    totalItems.value = response.count

    // Start polling if there are pending requests
    if (response.results.some((r) => r.status === 'PENDING' || r.status === 'PROCESSING')) {
      startHistoryPolling()
    }
  } catch (error) {
    console.error('Failed to load history:', error)
  }
}

function handleRowClick(record: EssayEvaluationDataBrief) {
  router.push({ name: 'result', params: { id: record.id } })
}

function navigateToEvaluation() {
  router.push({ name: 'evaluate' })
}

const handleRefresh = () => {
  loadData(currentPage.value)
}

// Lifecycle
onMounted(() => {
  loadData(1)
})
</script>

<template>
  <div class="result-list-view">
    <!-- Header Section -->
    <div class="result-list-header">
      <div class="result-list-header-content">
        <div class="result-list-title-section">
          <h1 class="result-list-title">
            <FileText class="result-list-title-icon" />
            Assessment Results
          </h1>
          <p class="result-list-subtitle">Click on a row to view detailed assessment results</p>
        </div>
        <Button @click="navigateToEvaluation" class="new-evaluation-button" size="lg">
          <Plus class="button-icon" />
          Evaluate
        </Button>
      </div>
    </div>

    <!-- Data Table Section -->
    <div class="result-list-content">
      <DataTable
        :data="data"
        :columns="columns"
        @row-click="handleRowClick"
        @refresh="handleRefresh"
      />
    </div>
  </div>
</template>

<style scoped>
/* Main Container */
.result-list-view {
  min-height: 100vh;
  padding: 2rem 1rem;
  background: hsl(var(--background));
}

@media (min-width: 768px) {
  .result-list-view {
    padding: 3rem 2rem;
  }
}

/* Header Section */
.result-list-header {
  margin-bottom: 2rem;
}

.result-list-header-content {
  max-width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  align-items: flex-start;
}

@media (min-width: 768px) {
  .result-list-header-content {
    flex-direction: row;
    justify-content: space-between;
    align-items: flex-end;
  }
}

/* Title Section */
.result-list-title-section {
  flex: 1;
}

.result-list-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.875rem;
  font-weight: 700;
  color: hsl(var(--foreground));
  margin-bottom: 0.5rem;
  line-height: 1.2;
}

.result-list-title-icon {
  width: 1.75rem;
  height: 1.75rem;
  color: hsl(var(--primary));
}

.result-list-subtitle {
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
  line-height: 1.5;
}

@media (min-width: 768px) {
  .result-list-title {
    font-size: 2.25rem;
  }

  .result-list-subtitle {
    font-size: 1rem;
  }
}

/* New Evaluation Button */
.new-evaluation-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.new-evaluation-button:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.button-icon {
  width: 1rem;
  height: 1rem;
}

/* Content Section */
.result-list-content {
  max-width: 100%;
  margin: 0 auto;
}
</style>
