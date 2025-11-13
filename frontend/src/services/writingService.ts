/**
 * Writing Service
 *
 * Service class for essay evaluation API operations.
 * Provides methods for submitting essays, fetching evaluations, and managing essay history.
 *
 * @class EssayService
 */

import api from '@/services/apiService'
import type { EssayRequest, EssayListResponse } from '@/models/writing'

export class EssayService {
  /**
   * Submit a new essay for evaluation
   *
   * Creates a new essay evaluation request and returns the request object
   * with status 'PENDING' or 'PROCESSING'.
   *
   * @param essay_text - The essay content to evaluate
   * @param essay_prompt - The essay topic/prompt
   * @returns Promise resolving to EssayRequest with initial status
   */
  public static async submitEssay({
    essay_text,
    essay_prompt,
  }: {
    essay_text: string,
    essay_prompt: string,
  }): Promise<EssayRequest> {
    const response = await api.post<EssayRequest>('/evaluate-essay/', {
      essay_text,
      essay_prompt,
    })
    return response.data
  }

  /**
   * Get detailed essay evaluation by request ID
   *
   * Fetches the complete evaluation data including:
   * - Surface-level corrections and comments
   * - Deep analysis (micro and macro comments)
   * - Score and corrected text
   *
   * @param requestId - The ID of the evaluation request
   * @returns Promise resolving to complete EssayRequest with evaluation data
   */
  public static async getEssayEvaluation(requestId: number): Promise<EssayRequest> {
    const response = await api.get<EssayRequest>(`/evaluate-essay/${requestId}/`)
    return response.data
  }

  /**
   * Get paginated list of essay evaluation history
   *
   * Returns a paginated list of brief evaluation data for display in tables/lists.
   * Includes status, essay text preview, score, and timestamps.
   *
   * @param page - Page number (1-indexed)
   * @param pageSize - Number of items per page
   * @returns Promise resolving to paginated EssayListResponse
   */
  public static async getEssayHistory(
    page: number = 1,
    pageSize: number = 10,
  ): Promise<EssayListResponse> {
    const response = await api.get<EssayListResponse>('/evaluate-essay/', {
      params: { page, page_size: pageSize },
    })
    return response.data
  }

  /**
   * Delete multiple essays in bulk
   *
   * Permanently deletes essay evaluation records by their IDs.
   * Used for bulk delete operations in the UI.
   *
   * @param ids - Array of essay evaluation IDs to delete
   * @returns Promise that resolves when deletion is complete
   */
  public static async deleteEssays(ids: number[]): Promise<void> {
    await api.post('/evaluate-essay/bulk_delete/', { ids })
  }
}
