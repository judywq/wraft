/**
 * useWritingPolling — composable hook
 *
 * Periodically checks essay evaluation history with an exponential backoff.
 * Stops automatically when there are no PENDING items left.
 * Cleans up timers when the owning component unmounts.
 *
 * Exposed API:
 *   - startPolling(options): begin polling immediately with backoff
 */

import { ref, onUnmounted } from 'vue'
import { EssayService } from '@/services/writingService'
import type { EssayEvaluationDataBrief } from '@/models/writing'
import { useToast } from '@/components/ui/toast/use-toast'

// backoff tuning
const INITIAL_DELAY = 500;   // 0.5s
const CEILING_DELAY = 10_000; // 10s

type PollOptions = {
  pageSize: number
  page: number
  onData: (rows: EssayEvaluationDataBrief[]) => void
  onStatusChange?: (row: EssayEvaluationDataBrief) => void
  onError?: (err: unknown) => void
}

export function useWritingPolling() {
  const { toast } = useToast()

  // holds current scheduled timeout so we can cancel/reschedule safely
  const timerId = ref<ReturnType<typeof setTimeout> | null>(null)

  // --- helpers ---------------------------------------------------------------

  const clearTimer = () => {
    if (timerId.value !== null) {
      clearTimeout(timerId.value)
      timerId.value = null
    }
  }

  const nextDelay = (attempt: number) =>
    Math.min(INITIAL_DELAY * Math.pow(2, attempt), CEILING_DELAY)

  // --- main entry ------------------------------------------------------------

  const startPolling = (opts: PollOptions) => {
    // ensure only a single poller is active
    clearTimer()

    let attempt = 0

    const tick = async () => {
      try {
        // 1) fetch a page of history
        const { results } = await EssayService.getEssayHistory(opts.page, opts.pageSize)

        // 2) hand off the data to the caller
        opts.onData(results)

        // 3) inform about any terminal states (matches original behavior:
        //    callback fires whenever an item is COMPLETED/FAILED, not only on transition)
        if (opts.onStatusChange) {
          for (const item of results) {
            if (item.status === 'COMPLETED' || item.status === 'FAILED') {
              opts.onStatusChange(item)
            }
          }
        }

        // 4) determine if we should continue polling (stop when no PENDING remain)
        const pendingExists = results.some(r => r.status === 'PENDING' || r.status === 'PROCESSING')
        if (!pendingExists) {
          clearTimer()
          return
        }

        // 5) schedule the next run with exponential backoff
        const delay = nextDelay(attempt)
        attempt += 1
        // eslint-disable-next-line no-console
        console.debug('[useWritingPolling] next poll in', delay, 'ms')
        timerId.value = setTimeout(tick, delay)
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error('[useWritingPolling] polling error:', err)

        clearTimer()
        opts.onError?.(err)

        toast({
          description: 'Failed to get evaluation status',
          variant: 'destructive',
        })
      }
    }

    // kick off immediately
    tick()
  }

  // --- lifecycle -------------------------------------------------------------

  onUnmounted(() => {
    clearTimer()
  })

  return { startPolling }
}
