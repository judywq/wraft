import { ref, onUnmounted } from 'vue'
import { EssayService } from '@/services/essayService'
import type { EssayEvaluationDataBrief } from '@/types/essay'
import { useToast } from '@/components/ui/toast/use-toast'

export function useEssayPolling() {
  const { toast } = useToast()
  const pollingInterval = ref<ReturnType<typeof setInterval> | null>(null)

  const startPolling = (options: {
    pageSize: number,
    page: number,
    onData: (data: EssayEvaluationDataBrief[]) => void,
    onStatusChange?: (request: EssayEvaluationDataBrief) => void,
    onError?: (error: any) => void
  }) => {
    // Clear any existing polling
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
    }

    let attempts = 0
    const baseDelay = 500 // Start with 0.5 second
    const maxDelay = 10000 // Max delay of 10 seconds

    const poll = async () => {
      try {
        const response = await EssayService.getEssayHistory(options.page, options.pageSize)
        const results = response.results

        // Call the data callback
        options.onData(results)

        // Check for status changes if callback provided
        if (options.onStatusChange) {
          results.forEach(request => {
            if (request.status === 'COMPLETED' || request.status === 'FAILED') {
              options.onStatusChange?.(request)
            }
          })
        }

        // Check if we need to continue polling
        const hasPendingRequests = results.some(r => r.status === 'PENDING')
        if (!hasPendingRequests) {
          if (pollingInterval.value) {
            clearInterval(pollingInterval.value)
            pollingInterval.value = null
          }
          return
        }

        // Calculate next delay with exponential backoff
        const delay = Math.min(baseDelay * Math.pow(2, attempts), maxDelay)
        attempts++
        console.debug('Polling again in', delay, 'ms')

        // Schedule next poll
        pollingInterval.value = setTimeout(poll, delay)
      } catch (err) {
        console.error('Error polling history:', err)
        if (pollingInterval.value) {
          clearTimeout(pollingInterval.value)
          pollingInterval.value = null
        }
        options.onError?.(err)
        toast({
          description: 'Failed to get evaluation status',
          variant: 'destructive',
        })
      }
    }

    // Start first poll immediately
    poll()
  }

  // Clean up polling when component is unmounted
  onUnmounted(() => {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
    }
  })

  return {
    startPolling
  }
}
