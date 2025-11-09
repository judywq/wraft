/**
 * Type Definitions for LLM Models
 *
 * @module types/llm
 */

/**
 * LLM Model configuration interface
 *
 * Represents an LLM model available in the system with usage limits.
 * Used for model selection and quota management.
 */
export interface LLMModel {
  /** Unique model identifier */
  id: number

  /** Display order for UI sorting */
  order: number

  /** Human-readable model name (e.g., "GPT-4", "Claude 3") */
  display_name: string

  /** Number of requests used today */
  used_limit: number

  /** Maximum number of requests allowed per day */
  daily_limit: number
}
