/**
 * useWritingPolling Composable
 *
 * Provides polling functionality for essay evaluation status updates.
 * Features:
 * - Exponential backoff polling strategy
 * - Automatic stop when no pending requests remain
 * - Status change callbacks for completed/failed evaluations
 * - Automatic cleanup on component unmount
 *
 * @returns {Object} Object containing startPolling function
 */

import { ref, onUnmounted } from 'vue'
import { EssayService } from '@/services/writingService'
import type { EssayEvaluationDataBrief } from '@/types/writing'
import { useToast } from '@/components/ui/toast/use-toast'

// Polling configuration constants
const BASE_DELAY_MS = 500 // Initial delay: 0.5 seconds
const MAX_DELAY_MS = 10000 // Maximum delay: 10 seconds

export function useWritingPolling() {
  const { toast } = useToast()

  /**
   * Reactive state: Stores the current polling interval/timeout ID
   * Used to clear polling when component unmounts or new polling starts
   */
  const pollingInterval = ref<ReturnType<typeof setInterval> | null>(null)

  /**
   * Start polling for essay evaluation status updates
   *
   * Polling strategy:
   * - Starts immediately on first call
   * - Uses exponential backoff: delay doubles each attempt (500ms, 1s, 2s, 4s, 8s, 10s max)
   * - Automatically stops when no PENDING requests are found
   * - Clears any existing polling before starting new one
   *
   * @param options - Polling configuration
   * @param options.pageSize - Number of items per page to fetch
   * @param options.page - Page number to fetch
   * @param options.onData - Callback invoked with fetched data on each poll
   * @param options.onStatusChange - Optional callback invoked when a request status changes to COMPLETED or FAILED
   * @param options.onError - Optional callback invoked on polling errors
   */
  const startPolling = (options: {
    pageSize: number,
    page: number,
    onData: (data: EssayEvaluationDataBrief[]) => void,
    onStatusChange?: (request: EssayEvaluationDataBrief) => void,
    onError?: (error: any) => void
  }) => {
    // Clear any existing polling to prevent multiple concurrent polls
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = null
    }

    let attempts = 0

    /**
     * Internal polling function
     * Fetches essay history, processes results, and schedules next poll if needed
     */
    const poll = async () => {
      try {
        // Fetch essay history from API
        const response = await EssayService.getEssayHistory(options.page, options.pageSize)
        const results = response.results

        // Invoke data callback with fetched results
        options.onData(results)

        // Check for status changes (COMPLETED or FAILED) and notify via callback
        if (options.onStatusChange) {
          results.forEach(request => {
            if (request.status === 'COMPLETED' || request.status === 'FAILED') {
              options.onStatusChange?.(request)
            }
          })
        }

        // Check if we need to continue polling
        // Stop if no pending requests remain
        const hasPendingRequests = results.some(r => r.status === 'PENDING')
        if (!hasPendingRequests) {
          if (pollingInterval.value) {
            clearInterval(pollingInterval.value)
            pollingInterval.value = null
          }
          return
        }

        // Calculate next delay using exponential backoff
        // Formula: min(baseDelay * 2^attempts, maxDelay)
        const delay = Math.min(BASE_DELAY_MS * Math.pow(2, attempts), MAX_DELAY_MS)
        attempts++
        console.debug('Polling again in', delay, 'ms')

        // Schedule next poll with calculated delay
        pollingInterval.value = setTimeout(poll, delay)
      } catch (err) {
        console.error('Error polling history:', err)

        // Clean up on error
        if (pollingInterval.value) {
          clearTimeout(pollingInterval.value)
          pollingInterval.value = null
        }

        // Invoke error callback if provided
        options.onError?.(err)

        // Show user-friendly error toast
        toast({
          description: 'Failed to get evaluation status',
          variant: 'destructive',
        })
      }
    }

    // Start first poll immediately (no delay)
    poll()
  }

  /**
   * Cleanup: Stop polling when component is unmounted
   * Prevents memory leaks and unnecessary API calls
   */
  onUnmounted(() => {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = null
    }
  })

  return {
    startPolling
  }
}
