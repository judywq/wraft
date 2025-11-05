export interface LLMModel {
  id: number
  order: number
  is_default: boolean
  display_name: string
  used_quota: number
  daily_limit: number
}
