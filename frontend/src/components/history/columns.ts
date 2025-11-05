import { type ColumnDef } from '@tanstack/vue-table'
import { h } from 'vue'
import type { EssayEvaluationDataBrief } from '@/types/essay'
import { Checkbox } from '@/components/ui/checkbox'

export const columns: ColumnDef<EssayEvaluationDataBrief>[] = [
  {
    id: 'select',
    header: ({ table }) => h(Checkbox, {
      'checked': table.getIsAllPageRowsSelected(),
      'onUpdate:checked': (value: boolean) => table.toggleAllPageRowsSelected(!!value),
      'ariaLabel': 'Select all',
    }),
    cell: ({ row }) => h(Checkbox, {
      'checked': row.getIsSelected(),
      'onUpdate:checked': (value: boolean) => row.toggleSelected(!!value),
      'ariaLabel': 'Select row',
    }),
    enableSorting: false,
    enableHiding: false,
  },
  {
    id: 'sequence',
    header: '#',
    cell: ({ row }) => {
      return row.index + 1
    },
  },
  {
    accessorKey: 'essay_text',
    header: 'Essay',
    cell: ({ row }) => {
      const essay_text = row.getValue('essay_text') as string
      return h(
        'div',
        { class: 'max-w-80 truncate' },
        essay_text,
      )
    },
  },
  {
    accessorKey: 'score',
    header: 'Score',
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => {
      const status = row.getValue('status') as string
      return h(
        'div',
        {
          class: {
            'text-green-600': status === 'COMPLETED',
            'text-red-600': status === 'FAILED',
            'text-yellow-600': status === 'PENDING',
          },
        },
        status,
      )
    },
  },
  {
    accessorKey: 'created_at',
    header: 'Created At',
    cell: ({ row }) => {
      return new Date(row.getValue('created_at')).toLocaleString()
    },
    sortingFn: 'datetime',
  },
]
