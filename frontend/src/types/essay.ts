export interface SurfaceComment {
  id: number
  end: number
  start: number
  reason: string
  error_type: string
  corrected_text: string
  highlighted_text: string
}

export interface MicroComment {
  id: number
  end: number
  type: string
  start: number
  comment: string
  paragraph_id: number
  paragraph_text: string
  highlighted_text: string
}

export interface MacroComment {
  id: number
  comment: string
  paragraph_id: number
  paragraph_text: string
}

export interface EssayEvaluationData {
  essay_prompt: string
  essay_text: string
  essay_text_corrected: string
  score: number | null
  surface: {
    text: string,
    comments: SurfaceComment[]
  }
  deep: {
    text: string
    micro_comments: MicroComment[]
    macro_comments: MacroComment[]
  }
}

export interface EssayRequest {
  id: number
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'ABORTED'
  error: string | null
  created_at: string
  updated_at: string
  evaluation: EssayEvaluationData
}

export interface EssayEvaluationDataBrief {
  id: number
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'ABORTED'
  essay_text: string
  score: number | null
  created_at: string
}

export interface EssayListResponse {
  count: number
  next: string | null
  previous: string | null
  results: EssayEvaluationDataBrief[]
}
