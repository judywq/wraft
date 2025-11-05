import api from '@/services/api'
import type { EssayRequest, EssayListResponse } from '@/types/essay'

export class EssayService {
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

  public static async getEssayEvaluation(requestId: number): Promise<EssayRequest> {
    const response = await api.get<EssayRequest>(`/evaluate-essay/${requestId}/`)
    return response.data
  }

  public static async getEssayHistory(
    page: number = 1,
    pageSize: number = 10,
  ): Promise<EssayListResponse> {
    const response = await api.get<EssayListResponse>('/evaluate-essay/', {
      params: { page, page_size: pageSize },
    })
    return response.data
  }

  public static async deleteEssays(ids: number[]): Promise<void> {
    await api.post('/evaluate-essay/bulk_delete/', { ids })
  }
}
