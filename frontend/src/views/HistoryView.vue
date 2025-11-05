<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { EssayService } from '@/services/essayService'
import { columns } from '@/components/history/columns'
import DataTable from '@/components/history/DataTable.vue'
import { Button } from '@/components/ui/button'
import { useRouter } from 'vue-router'
import { Plus } from 'lucide-vue-next'
import type { EssayEvaluationDataBrief } from '@/types/essay'
import { useEssayPolling } from '@/composables/useEssayPolling'

const router = useRouter()

const ITEMS_TO_RETRIEVE = 1000
const data = ref<EssayEvaluationDataBrief[]>([])
const totalItems = ref(0)
const currentPage = ref(1)
const selectedRecord = ref<EssayEvaluationDataBrief | null>(null)

const { startPolling } = useEssayPolling()

const startHistoryPolling = () => {
  startPolling({
    page: currentPage.value,
    pageSize: ITEMS_TO_RETRIEVE,
    onData: (results) => {
      data.value = results

      // Update dialog content if open
      if (selectedRecord.value) {
        const updatedRecord = results.find(r => r.id === selectedRecord.value?.id)
        if (updatedRecord) {
          selectedRecord.value = updatedRecord
        }
      }
    }
  })
}

async function loadData(page: number) {
  try {
    const response = await EssayService.getEssayHistory(page, ITEMS_TO_RETRIEVE)
    data.value = response.results
    totalItems.value = response.count

    // Start polling if there are pending requests
    if (response.results.some(r => r.status === 'PENDING')) {
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
  router.push({ name: 'evaluation' })
}

const handleRefresh = () => {
  loadData(currentPage.value)
}

onMounted(() => {
  loadData(1)
})
</script>

<template>
  <div class="container mx-auto">
    <div class="flex justify-between items-center mb-4">
      <div>
        <h1 class="text-2xl font-bold">Evaluation History</h1>
        <p class="text-sm text-muted-foreground">Click on a row to view the details.</p>
      </div>
      <Button @click="navigateToEvaluation">
        <Plus class="mr-2 h-4 w-4" />
        New Evaluation
      </Button>
    </div>

    <DataTable :data="data" :columns="columns" @row-click="handleRowClick" @refresh="handleRefresh" />
  </div>
</template>
