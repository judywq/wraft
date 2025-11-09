/**
 * Type Definitions for Writing/Essay Evaluation
 *
 * @module types/writing
 */

/**
 * Surface-level comment (grammar, spelling, style corrections)
 *
 * Represents a correction or comment at the surface level of the essay.
 * Includes character positions for highlighting in the UI.
 */
export interface SurfaceComment {
  /** Unique comment identifier */
  id: number

  /** End character position in essay text */
  end: number

  /** Start character position in essay text */
  start: number

  /** Explanation of the issue or correction */
  reason: string

  /** Type/category of error (e.g., "grammar", "spelling", "style") */
  error_type: string

  /** Suggested corrected text */
  corrected_text: string

  /** Text that was highlighted/flagged */
  highlighted_text: string
}

/**
 * Micro-level comment (sentence/paragraph-level analysis)
 *
 * Represents detailed feedback at the sentence or paragraph level.
 * Provides deeper analysis than surface comments.
 */
export interface MicroComment {
  /** Unique comment identifier */
  id: number

  /** End character position */
  end: number

  /** Comment type/category */
  type: string

  /** Start character position */
  start: number

  /** Comment text/feedback */
  comment: string

  /** ID of the paragraph this comment relates to */
  paragraph_id: number

  /** Full text of the paragraph */
  paragraph_text: string

  /** Specific text highlighted in the comment */
  highlighted_text: string
}

/**
 * Macro-level comment (essay-level analysis)
 *
 * Represents high-level feedback about overall essay structure,
 * organization, argumentation, etc.
 */
export interface MacroComment {
  /** Unique comment identifier */
  id: number

  /** Comment text providing essay-level feedback */
  comment: string

  /** ID of the paragraph this comment relates to */
  paragraph_id: number

  /** Full text of the paragraph */
  paragraph_text: string
}

/**
 * Complete essay evaluation data
 *
 * Contains all evaluation results including surface corrections,
 * deep analysis (micro/macro comments), score, and corrected text.
 */
export interface EssayEvaluationData {
  /** Original essay prompt/topic */
  essay_prompt: string

  /** Original essay text submitted by user */
  essay_text: string

  /** Essay text with all surface corrections applied */
  essay_text_corrected: string

  /** Overall essay score (null if not yet scored) */
  score: number | null

  /** Surface-level analysis (grammar, spelling, style) */
  surface: {
    /** Processed text with surface corrections */
    text: string
    /** Array of surface-level comments/corrections */
    comments: SurfaceComment[]
  }

  /** Deep-level analysis (structure, argumentation, content) */
  deep: {
    /** Processed text for deep analysis */
    text: string
    /** Sentence/paragraph-level comments */
    micro_comments: MicroComment[]
    /** Essay-level comments */
    macro_comments: MacroComment[]
  }
}

/**
 * Essay evaluation request
 *
 * Represents a single essay evaluation request with its status
 * and complete evaluation data (when available).
 */
export interface EssayRequest {
  /** Unique request identifier */
  id: number

  /** Current processing status */
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'

  /** Error message if status is FAILED, null otherwise */
  error: string | null

  /** ISO timestamp when request was created */
  created_at: string

  /** ISO timestamp when request was last updated */
  updated_at: string

  /** Complete evaluation data (only available when status is COMPLETED) */
  evaluation: EssayEvaluationData
}

/**
 * Brief essay evaluation data for lists/tables
 *
 * Lightweight version of EssayRequest used for displaying
 * evaluation history in tables without full evaluation data.
 */
export interface EssayEvaluationDataBrief {
  /** Unique request identifier */
  id: number

  /** Current processing status */
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'

  /** Essay text (may be truncated for display) */
  essay_text: string

  /** Overall essay score (null if not yet scored) */
  score: number | null

  /** ISO timestamp when request was created */
  created_at: string
}

/**
 * Paginated essay list response
 *
 * Standard pagination response structure for essay evaluation history.
 */
export interface EssayListResponse {
  /** Total number of items across all pages */
  count: number

  /** URL to next page (null if no next page) */
  next: string | null

  /** URL to previous page (null if no previous page) */
  previous: string | null

  /** Array of brief evaluation data for current page */
  results: EssayEvaluationDataBrief[]
}
