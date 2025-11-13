<script setup lang="ts" generic="TData extends { id: number }">
/**
 * Enhanced DataTable Component
 *
 * A modern, feature-rich data table built on TanStack Table (Vue).
 * Capabilities:
 * - Advanced sorting, pagination, and multi-row selection
 * - Batch operations with confirmation modal
 * - Interactive row navigation (checkbox clicks excluded)
 * - Parent component refresh notifications
 *
 * @generic TData - Data type requiring an `id: number` property
 */

import { computed, ref } from 'vue'
import { type ColumnDef } from '@tanstack/vue-table'
import {
  useVueTable,
  getSortedRowModel,
  getPaginationRowModel,
  getCoreRowModel,
  FlexRender,
} from '@tanstack/vue-table'

import { Button } from '@/components/ui/button'
import {
  TableRow,
  TableHeader,
  TableHead,
  TableCell,
  TableBody,
  Table,
} from '@/components/ui/table'
import { useToast } from '@/components/ui/toast/use-toast'
import {
  DialogFooter,
  DialogDescription,
  DialogTitle,
  DialogHeader,
  DialogContent,
  Dialog,
} from '@/components/ui/dialog'
import { EssayService } from '@/services/writingService'

// Configuration
const PAGE_SIZE = 10

// Component interface
const componentProps = defineProps<{
  data: TData[]
  columns: ColumnDef<TData, any>[]
}>()

// Event definitions
const eventEmitter = defineEmits<{
  (e: 'refresh'): void
  (e: 'rowClick', item: TData): void
}>()

// Toast notification system
const notificationSystem = useToast()
const { toast } = notificationSystem

// UI state management
const isDeletionModalVisible = ref(false)
const currentPageState = ref({
  pageSize: PAGE_SIZE,
  pageIndex: 0,
})
const sortConfiguration = ref([{ desc: true, id: 'created_at' }])

/**
 * Computed property: Track number of selected items
 */
const activeSelectionCount = computed(() => {
  return dataTableInstance.getSelectedRowModel().rows.length
})

/**
 * Table instance initialization
 * Manages sorting, pagination, and selection state
 */
const dataTableInstance = useVueTable({
  enableMultiRowSelection: true,
  enableRowSelection: true,
  getCoreRowModel: getCoreRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  getSortedRowModel: getSortedRowModel(),
  state: {
    get pagination() {
      return currentPageState.value
    },
    get sorting() {
      return sortConfiguration.value
    },
  },
  onPaginationChange: pageUpdater => {
    currentPageState.value =
      typeof pageUpdater === 'function'
        ? pageUpdater(currentPageState.value)
        : pageUpdater
  },
  get data() {
    return componentProps.data
  },
  get columns() {
    return componentProps.columns
  },
})

/**
 * Process row click interactions
 * Filters out checkbox column clicks to prevent navigation conflicts
 *
 * @param clickEvent - Browser mouse event
 * @param dataItem - Associated data record
 */
const processRowInteraction = (clickEvent: MouseEvent, dataItem: TData) => {
  const clickedElement = clickEvent.target as HTMLElement
  const tableCell = clickedElement.closest('td')

  // Skip navigation for selection column (index 0)
  if (tableCell?.cellIndex === 0) {
    return
  }

  eventEmitter('rowClick', dataItem)
}

/**
 * Trigger deletion workflow
 * Validates selection before opening confirmation modal
 */
const initiateDeletion = () => {
  if (activeSelectionCount.value === 0) {
    toast({
      variant: 'destructive',
      description: 'Please select items to delete',
      title: 'No items selected',
    })
    return
  }
  isDeletionModalVisible.value = true
}

/**
 * Execute confirmed deletion operation
 * Performs API call, updates UI, and notifies parent
 */
const executeDeletion = async () => {
  isDeletionModalVisible.value = false

  const chosenRows = dataTableInstance.getSelectedRowModel().rows
  const itemIdentifiers = chosenRows.map(row => row.original.id)

  try {
    await EssayService.deleteEssays(itemIdentifiers)
    dataTableInstance.toggleAllRowsSelected(false)
    eventEmitter('refresh')
    toast({
      description: `Deleted ${itemIdentifiers.length} items`,
      title: 'Success',
    })
  } catch (error) {
    toast({
      variant: 'destructive',
      description: 'Failed to delete selected items',
      title: 'Error',
    })
  }
}
</script>

<template>
  <div class="data-table-container">
    <!-- Action toolbar -->
    <div class="action-toolbar">
      <Button
        size="sm"
        variant="destructive"
        :disabled="activeSelectionCount === 0"
        @click="initiateDeletion"
        class="delete-action-button"
      >
        <span class="button-text">Remove Selected</span>
        <span v-if="activeSelectionCount > 0" class="selection-badge">
          {{ activeSelectionCount }}
        </span>
      </Button>
    </div>

    <!-- Table wrapper with enhanced styling -->
    <div class="table-wrapper">
      <Table class="enhanced-table">
        <TableHeader class="table-header-section">
          <TableRow
            v-for="headerGroup in dataTableInstance.getHeaderGroups()"
            :key="headerGroup.id"
            class="header-row"
          >
            <TableHead
              v-for="header in headerGroup.headers"
              :key="header.id"
              class="header-cell"
            >
              <FlexRender
                v-if="!header.isPlaceholder"
                :props="header.getContext()"
                :render="header.column.columnDef.header"
              />
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody class="table-body-section">
          <TableRow
            v-for="row in dataTableInstance.getRowModel().rows"
            :key="row.id"
            class="data-row"
            @click="(event: MouseEvent) => processRowInteraction(event, row.original)"
          >
            <TableCell
              v-for="cell in row.getVisibleCells()"
              :key="cell.id"
              class="data-cell"
            >
              <FlexRender
                :props="cell.getContext()"
                :render="cell.column.columnDef.cell"
              />
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>

    <!-- Pagination controls -->
    <div class="pagination-container">
      <div class="pagination-info">
        <span class="page-indicator">
          Showing page {{ dataTableInstance.getState().pagination.pageIndex + 1 }} of
          {{ dataTableInstance.getPageCount() }}
        </span>
      </div>
      <div class="pagination-buttons">
        <Button
          size="sm"
          variant="outline"
          :disabled="!dataTableInstance.getCanPreviousPage()"
          @click="dataTableInstance.previousPage()"
          class="nav-button"
        >
          ← Previous
        </Button>
        <Button
          size="sm"
          variant="outline"
          :disabled="!dataTableInstance.getCanNextPage()"
          @click="dataTableInstance.nextPage()"
          class="nav-button"
        >
          Next →
        </Button>
      </div>
    </div>

    <!-- Deletion confirmation modal -->
    <Dialog
      :open="isDeletionModalVisible"
      @update:open="isDeletionModalVisible = false"
    >
      <DialogContent class="deletion-modal">
        <DialogHeader>
          <DialogTitle>Confirm Deletion</DialogTitle>
          <DialogDescription>
            You are about to permanently delete
            {{ activeSelectionCount }} {{ activeSelectionCount === 1 ? 'item' : 'items' }}.
            This action cannot be reversed.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            variant="outline"
            @click="isDeletionModalVisible = false"
            class="cancel-button"
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            @click="executeDeletion"
            class="confirm-button"
          >
            Confirm Delete
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<style scoped>
.data-table-container {
  @apply w-full space-y-6;
}

.action-toolbar {
  @apply flex items-center justify-between p-4 bg-card rounded-lg border shadow-sm;
}

.delete-action-button {
  @apply relative flex items-center gap-2 transition-all duration-200;
}

.delete-action-button:hover:not(:disabled) {
  @apply scale-105 shadow-md;
}

.selection-badge {
  @apply ml-2 px-2 py-0.5 text-xs font-semibold bg-white text-red-600 rounded-full border border-red-300;
}

.table-wrapper {
  @apply rounded-lg border bg-card shadow-sm overflow-hidden;
}

.enhanced-table {
  @apply w-full;
}

.table-header-section {
  @apply bg-purple-600/80;
}

.header-row {
  @apply border-b border-purple-500/50;
}

.header-cell {
  @apply font-semibold text-white py-4 px-4;
}

.table-body-section {
  @apply divide-y divide-border;
}

.data-row {
  @apply cursor-pointer transition-colors duration-150 border-b border-border/50;
}

.data-row:hover {
  @apply bg-muted/30;
}

.data-row:active {
  @apply bg-muted/50;
}

.data-cell {
  @apply py-3 px-4 text-sm;
}

.pagination-container {
  @apply flex flex-col sm:flex-row items-center justify-between gap-4 p-4 bg-card rounded-lg border shadow-sm;
}

.pagination-info {
  @apply flex items-center;
}

.page-indicator {
  @apply text-sm text-muted-foreground font-medium;
}

.pagination-buttons {
  @apply flex items-center gap-2;
}

.nav-button {
  @apply min-w-[100px] transition-all duration-200;
}

.nav-button:hover:not(:disabled) {
  @apply shadow-md;
}

.deletion-modal {
  @apply max-w-md;
}

.cancel-button,
.confirm-button {
  @apply min-w-[100px];
}
</style>
