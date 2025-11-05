<script setup lang="ts" generic="TData extends { id: number }">
import { type ColumnDef } from '@tanstack/vue-table'
import {
  FlexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useVueTable,
} from '@tanstack/vue-table'
import { ref, computed } from 'vue'

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast/use-toast'
import { EssayService } from '@/services/essayService'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'

const ITEMS_PER_PAGE = 10
const props = defineProps<{
  columns: ColumnDef<TData, any>[]
  data: TData[]
}>()

const emit = defineEmits<{
  (e: 'rowClick', record: TData): void
  (e: 'refresh'): void
}>()

const { toast } = useToast()
const showConfirmDialog = ref(false)
const sorting = ref([{ id: 'created_at', desc: true }])
const pagination = ref({
  pageIndex: 0,
  pageSize: ITEMS_PER_PAGE,
})

const table = useVueTable({
  get data() {
    return props.data
  },
  get columns() {
    return props.columns
  },
  getCoreRowModel: getCoreRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  getSortedRowModel: getSortedRowModel(),
  state: {
    get sorting() {
      return sorting.value
    },
    get pagination() {
      return pagination.value
    },
  },
  // https://tanstack.com/table/latest/docs/framework/vue/guide/table-state#individual-controlled-state
  onPaginationChange: updater => {
    pagination.value =
      updater instanceof Function
        ? updater(pagination.value)
        : updater
  },
  enableRowSelection: true,
  enableMultiRowSelection: true,
})

const selectedCount = computed(() => table.getSelectedRowModel().rows.length)

const handleConfirmDelete = async () => {
  showConfirmDialog.value = false

  const selectedRows = table.getSelectedRowModel().rows

  const ids = selectedRows.map(row => row.original.id)
  try {
    await EssayService.deleteEssays(ids)
    emit('refresh')
    table.toggleAllRowsSelected(false)
    toast({
      title: 'Success',
      description: `Deleted ${ids.length} items`,
    })
  } catch (error) {
    toast({
      title: 'Error',
      description: 'Failed to delete selected items',
      variant: 'destructive',
    })
  }
}

const handleDelete = () => {
  if (selectedCount.value === 0) {
    toast({
      title: 'No items selected',
      description: 'Please select items to delete',
      variant: 'destructive',
    })
    return
  }
  showConfirmDialog.value = true
}

const handleRowClick = (event: MouseEvent, record: TData) => {
  // Check if the click originated from the selection column
  const target = event.target as HTMLElement
  const cell = target.closest('td')

  // The selection column has the first checkbox, so it will be the first cell
  if (cell?.cellIndex === 0) {
    return
  }

  emit('rowClick', record)
}
</script>

<template>
  <div>
    <div class="mb-4">
      <Button
        variant="destructive"
        size="sm"
        :disabled="selectedCount === 0"
        @click="handleDelete"
      >
        Delete Selected
      </Button>
    </div>
    <div class="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
            <TableHead v-for="header in headerGroup.headers" :key="header.id">
              <FlexRender
                v-if="!header.isPlaceholder"
                :render="header.column.columnDef.header"
                :props="header.getContext()"
              />
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow
            v-for="row in table.getRowModel().rows"
            :key="row.id"
            class="cursor-pointer hover:bg-muted/50"
            @click="(event) => handleRowClick(event, row.original)"
          >
            <TableCell v-for="cell in row.getVisibleCells()" :key="cell.id">
              <FlexRender :render="cell.column.columnDef.cell" :props="cell.getContext()" />
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>

    <div class="flex items-center justify-end space-x-2 py-4">
      <div class="flex items-center gap-2">
        <p class="text-sm text-muted-foreground">
          Page {{ table.getState().pagination.pageIndex + 1 }} of {{ table.getPageCount() }}
        </p>
      </div>
      <Button
        variant="outline"
        size="sm"
        :disabled="!table.getCanPreviousPage()"
        @click="table.previousPage()"
      >
        Previous
      </Button>
      <Button
        variant="outline"
        size="sm"
        :disabled="!table.getCanNextPage()"
        @click="table.nextPage()"
      >
        Next
      </Button>
    </div>

    <Dialog :open="showConfirmDialog" @update:open="showConfirmDialog = false">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Confirm Deletion</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete {{ selectedCount }} selected {{ selectedCount === 1 ? 'item' : 'items' }}?
            This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            variant="outline"
            @click="showConfirmDialog = false"
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            @click="handleConfirmDelete"
          >
            Delete
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
