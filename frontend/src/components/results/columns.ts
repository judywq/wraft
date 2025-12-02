import { h } from 'vue'
import { type ColumnDef } from '@tanstack/vue-table'
import type { EssayEvaluationDataBrief } from '@/models/writing'
import { Checkbox } from '@/components/ui/checkbox'

export const columns: ColumnDef<EssayEvaluationDataBrief>[] = [
  {
    id: 'select',
    enableHiding: false,
    enableSorting: false,
    header: ({ table }) => {
      return h(Checkbox, {
        ariaLabel: 'Select all rows',
        checked: table.getIsAllPageRowsSelected(),
        'onUpdate:checked': (value: boolean) => {
          table.toggleAllPageRowsSelected(!!value)
        },
      })
    },
    cell: ({ row }) => {
      return h(Checkbox, {
        ariaLabel: 'Select row',
        checked: row.getIsSelected(),
        'onUpdate:checked': (value: boolean) => {
          row.toggleSelected(!!value)
        },
      })
    },
  },
  {
    id: 'sequence',
    header: () => h('span', { class: 'font-semibold text-white' }, '#'),
    cell: ({ row }) => {
      const sequenceNumber = row.index + 1
      return h(
        'span',
        {
          class: 'text-sm text-foreground',
        },
        sequenceNumber.toString(),
      )
    },
  },
  {
    accessorKey: 'essay_text',
    header: () => h('span', { class: 'font-semibold text-white' }, 'Essay Content'),
    cell: ({ row }) => {
      const content = row.getValue('essay_text') as string
      return h(
        'div',
        {
          class: 'max-w-md pr-4',
        },
        [
          h(
            'p',
            {
              class: 'text-sm text-foreground line-clamp-2 leading-relaxed',
              title: content,
            },
            content || 'No content available',
          ),
        ],
      )
    },
  },
  {
    accessorKey: 'score',
    header: () => h('span', { class: 'font-semibold text-white' }, 'Score'),
    cell: ({ row }) => {
      const scoreValue = row.getValue('score') as number | null
      const displayScore = scoreValue !== null ? scoreValue.toFixed(1) : 'N/A'
      return h(
        'span',
        {
          class: 'text-sm text-foreground',
        },
        displayScore,
      )
    },
  },
  {
    accessorKey: 'status',
    header: () => h('span', { class: 'font-semibold text-white' }, 'Status'),
    cell: ({ row }) => {
      const currentStatus = row.getValue('status') as string
      const statusConfig = {
        COMPLETED: {
          class: 'bg-green-500 text-white border-green-600',
          label: 'Completed',
        },
        FAILED: {
          class: 'bg-red-500 text-white border-red-600',
          label: 'Failed',
        },
        PENDING: {
          class: 'bg-yellow-500 text-white border-yellow-600',
          label: 'Pending',
        },
      }
      const config = statusConfig[currentStatus as keyof typeof statusConfig] || {
        class: 'bg-gray-500 text-white border-gray-600',
        label: currentStatus,
      }
      return h(
        'span',
        {
          class: `inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${config.class}`,
        },
        config.label,
      )
    },
  },
  {
    accessorKey: 'created_at',
    header: () => h('span', { class: 'font-semibold text-white' }, 'Created Date'),
    sortingFn: 'datetime',
    cell: ({ row }) => {
      const timestamp = row.getValue('created_at') as string
      const dateObj = new Date(timestamp)
      const formattedDate = dateObj.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
      const formattedTime = dateObj.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      })
      return h(
        'div',
        {
          class: 'flex flex-col gap-1',
        },
        [
          h(
            'span',
            {
              class: 'text-sm font-medium text-foreground',
            },
            formattedDate,
          ),
          h(
            'span',
            {
              class: 'text-xs text-muted-foreground',
            },
            formattedTime,
          ),
        ],
      )
    },
  },
]
