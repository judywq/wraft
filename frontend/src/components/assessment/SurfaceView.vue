<template>
  <div class="view-content">
    <div class="toggle-container">
      <button
        class="toggle-btn"
        :class="{ active: currentView === 'original' }"
        @click="$emit('update-view', 'original')"
      >
        Original
      </button>
      <button
        class="toggle-btn"
        :class="{ active: currentView === 'track-changes' }"
        @click="$emit('update-view', 'track-changes')"
      >
        Track Changes
      </button>
      <button
        class="toggle-btn"
        :class="{ active: currentView === 'corrected' }"
        @click="$emit('update-view', 'corrected')"
      >
        Corrected
      </button>
    </div>

    <!-- Loading state for comments -->
    <div v-if="shouldShowLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading surface feedback...</p>
    </div>

    <!-- Completed state with no comments -->
    <div v-else-if="isCompleted && !hasSurfaceComments" class="completed-empty-container">
      <div class="completed-message">
        <p class="completed-title">Surface feedback completed</p>
        <p class="completed-description">
          No surface-level corrections were found. Your essay looks good!
        </p>
      </div>
      <div class="content-layout">
        <div class="text-column">
          <div class="text-container" id="surface-text-container">
            <div v-for="(paragraph, index) in paragraphs" :key="index">
              <p :style="{ marginBottom: '1rem' }">{{ paragraph }}</p>
            </div>
          </div>
        </div>
        <div class="comment-column">
          <div class="comment-sticky" id="surface-comment-container">
            <div class="no-comment-message">No surface-level corrections found</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Content with comments or completed status (fallback if status undefined but has data) -->
    <div v-else class="content-layout">
      <div class="text-column">
        <div class="text-container" id="surface-text-container">
          <div v-for="(paragraph, index) in paragraphs" :key="index">
            <p :style="{ marginBottom: '1rem' }">
              <span
                v-for="(segment, segIndex) in getParagraphSegments(paragraph, index)"
                :key="segIndex"
              >
                <template
                  v-if="
                    segment.comment &&
                    currentView === 'track-changes' &&
                    segment.comment.corrected_text
                  "
                >
                  <span
                    class="error"
                    :data-comment-id="segment.comment.id"
                    :data-comment-data="segment.comment.reason"
                    :data-original-text="segment.text"
                    :data-corrected-text="segment.comment.corrected_text"
                    @mouseenter="handleSurfaceMouseEnter"
                    @mouseleave="handleSurfaceMouseLeave"
                    @click="handleSurfaceClick"
                  >
                    {{ segment.text }}
                  </span>
                  <span
                    class="correction"
                    :data-comment-id="segment.comment.id"
                    :data-comment-data="segment.comment.reason"
                    :data-original-text="segment.text"
                    :data-corrected-text="segment.comment.corrected_text"
                    @mouseenter="handleSurfaceMouseEnter"
                    @mouseleave="handleSurfaceMouseLeave"
                    @click="handleSurfaceClick"
                  >
                    {{ segment.comment.corrected_text }}
                  </span>
                </template>
                <template
                  v-else-if="
                    segment.comment &&
                    currentView === 'track-changes' &&
                    !segment.comment.corrected_text
                  "
                >
                  <span
                    class="error"
                    :data-comment-id="segment.comment.id"
                    :data-comment-data="segment.comment.reason"
                    :data-original-text="segment.text"
                    :data-corrected-text="segment.comment.corrected_text"
                    @mouseenter="handleSurfaceMouseEnter"
                    @mouseleave="handleSurfaceMouseLeave"
                    @click="handleSurfaceClick"
                  >
                    {{ segment.text }}
                  </span>
                </template>
                <template v-else-if="segment.comment && currentView === 'corrected'">
                  <template v-if="segment.comment.corrected_text">
                    <span
                      :class="getSegmentClasses(segment)"
                      :data-comment-id="segment.comment.id"
                      :data-comment-data="segment.comment.reason"
                      :data-original-text="segment.text"
                      :data-corrected-text="segment.comment.corrected_text"
                      @mouseenter="handleSurfaceMouseEnter"
                      @mouseleave="handleSurfaceMouseLeave"
                      @click="handleSurfaceClick"
                    >
                      {{ segment.comment.corrected_text }}
                    </span>
                  </template>
                  <!-- deletion segments (no corrected_text) are hidden in Corrected view -->
                </template>
                <span
                  v-else-if="segment.comment && currentView === 'original'"
                  :class="getSegmentClasses(segment)"
                  :data-comment-id="segment.comment.id"
                  :data-comment-data="segment.comment.reason"
                  :data-original-text="segment.text"
                  :data-corrected-text="segment.comment.corrected_text"
                  @mouseenter="handleSurfaceMouseEnter"
                  @mouseleave="handleSurfaceMouseLeave"
                  @click="handleSurfaceClick"
                >
                  {{ segment.text }}
                </span>
                <span v-else>
                  {{ segment.text }}
                </span>
                <span v-if="segIndex < getParagraphSegments(paragraph, index).length - 1"
                  >&nbsp;</span
                >
              </span>
            </p>
          </div>
        </div>
      </div>

      <div class="comment-column">
        <div class="comment-sticky" id="surface-comment-container">
          <div v-if="!lockedComment" class="no-comment-message">
            Hover over highlighted text to view comments
          </div>
          <div v-else class="comment-item">
            <div class="comparison-box">
              <span
                class="error-box"
                :style="{
                  fontStyle: isInsertion ? 'italic' : '',
                  color: isInsertion ? '#999' : '',
                }"
              >
                {{ isInsertion ? '[No text]' : lockedComment.originalText }}
              </span>
              <span class="arrow">→</span>
              <span
                class="correction-box"
                :style="{ fontStyle: isDeletion ? 'italic' : '', color: isDeletion ? '#999' : '' }"
              >
                {{ isDeletion ? '[Deleted]' : lockedComment.correctedText }}
              </span>
            </div>
            <div class="comment-data">
              {{ lockedComment.commentData }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { EssayEvaluationData, SurfaceComment } from '@/models/writing'
import { PARAGRAPH_DELIMITER } from '@/lib/utils'

const props = defineProps<{
  evaluationData: EssayEvaluationData
  status?: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
  currentView: string
}>()

const emit = defineEmits<{
  (e: 'update-view', view: string): void
}>()

const lockedComment = ref<{
  id: string
  originalText: string
  correctedText: string
  commentData: string
} | null>(null)

const isSurfaceLocked = ref(false)

const paragraphs = computed(() => {
  return props.evaluationData?.essay_text?.split(PARAGRAPH_DELIMITER)
})

const hasSurfaceComments = computed(() => {
  return props.evaluationData?.surface?.comments && props.evaluationData.surface.comments.length > 0
})

const isProcessing = computed(() => {
  return props.status === 'PENDING' || props.status === 'PROCESSING'
})

const isCompleted = computed(() => {
  return props.status === 'COMPLETED'
})

const shouldShowLoading = computed(() => {
  // Show loading if processing and no comments yet
  // Also show loading if status is undefined and no comments (fallback case)
  if (isProcessing.value && !hasSurfaceComments.value) {
    return true
  }
  // If status is undefined/null and we have no comments, show loading as fallback
  if (!props.status && !hasSurfaceComments.value) {
    return true
  }
  return false
})

const isInsertion = computed(() => {
  return lockedComment.value?.originalText === ''
})

const isDeletion = computed(() => {
  return lockedComment.value?.correctedText === ''
})

interface Segment {
  text: string
  start?: number
  end?: number
  comment?: SurfaceComment & {
    wordStart: number
    wordEnd: number
  }
}

function getParagraphSegments(paragraphText: string, paragraphIndex: number): Segment[] {
  if (!props.evaluationData.surface.comments) {
    return [{ text: paragraphText }]
  }

  const comments = props.evaluationData.surface.comments
    .filter((comment) => {
      const startPos = comment.start
      const endPos = comment.end
      const paragraphStart = getParagraphStartPosition(paragraphIndex)
      const paragraphEnd = paragraphStart + paragraphText.trim().split(/\s+/).length
      return startPos >= paragraphStart && endPos <= paragraphEnd
    })
    .map((comment) => ({
      ...comment,
      wordStart: comment.start - getParagraphStartPosition(paragraphIndex),
      wordEnd: comment.end - getParagraphStartPosition(paragraphIndex),
    }))

  if (comments.length === 0) {
    return [{ text: paragraphText }]
  }

  const wordCount = paragraphText.trim().split(/\s+/).length
  const breaks = new Set([0, wordCount])

  comments.forEach((comment) => {
    breaks.add(comment.wordStart)
    breaks.add(comment.wordEnd)
  })

  const sortedBreaks = Array.from(breaks).sort((a, b) => a - b)
  const segments: Segment[] = []

  for (let i = 0; i < sortedBreaks.length - 1; i++) {
    const start = sortedBreaks[i]
    const end = sortedBreaks[i + 1]
    if (start === undefined || end === undefined) continue
    const text = wordSubstring(paragraphText, start, end)

    const segmentComments = comments.filter(
      (comment) => comment.wordStart <= start && comment.wordEnd >= end,
    )

    segments.push({
      text,
      start,
      end,
      comment: segmentComments.length > 0 ? segmentComments[0] : undefined,
    })
  }

  // Insert insertion segments so that addition corrections are displayed in the text
  const insertionComments = comments.filter((comment) => comment.wordStart === comment.wordEnd)
  insertionComments.forEach((comment) => {
    // Determine where to insert the empty-original segment for insertion
    let insertionIndex = segments.findIndex((seg) => seg.end === comment.wordStart)
    if (insertionIndex !== -1) {
      insertionIndex = insertionIndex + 1
    } else {
      insertionIndex = segments.findIndex((seg) => seg.start === comment.wordStart)
      if (insertionIndex === -1) {
        insertionIndex = segments.length
      }
    }
    segments.splice(insertionIndex, 0, {
      text: '',
      start: comment.wordStart,
      end: comment.wordEnd,
      comment,
    })
  })

  return segments
}

function getParagraphStartPosition(paragraphIndex: number) {
  let position = 0
  for (let i = 0; i < paragraphIndex; i++) {
    const paragraph = paragraphs.value[i]
    if (paragraph) {
      position += paragraph.trim().split(/\s+/).length
    }
  }
  return position
}

function wordSubstring(text: string, startWordIndex: number, endWordIndex: number) {
  const words = text.split(/\s+/)
  const selectedWords = words.slice(startWordIndex, endWordIndex)
  return selectedWords.join(' ')
}

function getSegmentClasses(segment: Segment) {
  const classes = []

  if (props.currentView === 'track-changes') {
    if (segment.comment?.corrected_text) {
      classes.push('error')
    }
  } else if (props.currentView === 'original') {
    if (segment.comment?.corrected_text) {
      classes.push('highlighted-only')
    }
  } else if (props.currentView === 'corrected') {
    if (segment.comment?.corrected_text) {
      classes.push('corrected-only')
    } else if (!segment.comment?.corrected_text && !segment.text) {
      return ''
    }
  }

  return classes.join(' ')
}

function handleSurfaceClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  const commentId = target.dataset.commentId ?? ''
  const originalText = target.dataset.originalText ?? ''
  const correctedText = target.dataset.correctedText ?? ''
  const commentData = target.dataset.commentData ?? ''

  if (!commentId || !commentData) return

  if (isSurfaceLocked.value && lockedComment.value?.id === commentId) {
    isSurfaceLocked.value = false
  } else {
    lockedComment.value = {
      id: commentId,
      originalText,
      correctedText,
      commentData,
    }
    isSurfaceLocked.value = true
  }
}

function handleSurfaceMouseEnter(event: MouseEvent) {
  const target = event.target as HTMLElement
  const commentId = target.dataset.commentId ?? ''
  const originalText = target.dataset.originalText ?? ''
  const correctedText = target.dataset.correctedText ?? ''
  const commentData = target.dataset.commentData ?? ''

  if (!commentId || !commentData) return

  if (!isSurfaceLocked.value) {
    lockedComment.value = {
      id: commentId,
      originalText,
      correctedText,
      commentData,
    }
  }
}

function handleSurfaceMouseLeave(event: MouseEvent) {
  const target = event.target as HTMLElement
  const commentId = target.dataset.commentId

  if (!commentId) return

  if (!isSurfaceLocked.value) {
    lockedComment.value = null
  }
}
</script>

<style scoped>
.view-content {
  margin-top: 20px;
}

.content-layout {
  position: relative;
  width: 100%;
}

.text-column {
  width: 55% !important;
  margin: 0 auto !important;
  position: relative;
}

.text-container {
  color: var(--primary-color);
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  line-height: 1.8;
}

.comment-column {
  position: fixed;
  top: 40%;
  right: 5%;
  width: 17%;
  z-index: 100;
}

.comment-sticky {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 15px;
  overflow-y: auto;
  max-height: calc(100vh - 300px);
}

.no-comment-message {
  color: #999;
  font-style: italic;
  text-align: center;
  padding: 20px 0;
}

.comment-item {
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid var(--border-color);
}

.comment-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.comparison-box {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  flex-wrap: wrap;
  gap: 10px;
}

.error-box {
  font-weight: bold;
  background-color: #f8d7da;
  color: #721c24;
  padding: 6px 10px;
  border-radius: 4px;
  font-family: 'Segoe UI';
  margin-right: 10px;
  word-wrap: break-word;
  word-break: break-word;
  max-width: 100%;
}

.arrow {
  color: #666;
  font-weight: bold;
  margin: 0 10px;
}

.correction-box {
  font-weight: bold;
  background-color: #d4edda;
  color: #155724;
  padding: 6px 10px;
  border-radius: 4px;
  font-family: 'Segoe UI';
}

.comment-data {
  font-size: 14px;
  color: #4a5568;
  line-height: 1.6;
  word-wrap: break-word;
}

.toggle-container {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.toggle-btn {
  background-color: #f1f5f9;
  color: #64748b;
  border: 1px solid #cbd5e1;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.toggle-btn:first-child {
  border-radius: 4px 0 0 4px;
}

.toggle-btn:last-child {
  border-radius: 0 4px 4px 0;
}

.toggle-btn.active {
  background-color: #2c5282;
  color: white;
  border-color: #2c5282;
}

.toggle-btn:hover:not(.active) {
  background-color: #e2e8f0;
}

.error {
  background-color: var(--error-color);
  text-decoration: line-through;
  text-decoration-color: red;
  border-radius: 2px;
  cursor: default;
}

.correction {
  background-color: var(--correction-color);
  text-decoration: underline;
  text-decoration-color: green;
  border-radius: 2px;
  margin-left: 0.2em;
  margin-right: 0.2em;
  cursor: default;
}

.highlighted-only {
  background-color: var(--error-color);
  border-radius: 2px;
  cursor: default;
}

.corrected-only {
  background-color: var(--correction-color);
  border-radius: 2px;
  cursor: default;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.completed-empty-container {
  margin-top: 20px;
}

.completed-message {
  text-align: center;
  padding: 20px;
  margin-bottom: 20px;
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 8px;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.completed-title {
  font-size: 18px;
  font-weight: bold;
  color: #155724;
  margin: 0 0 10px 0;
}

.completed-description {
  font-size: 14px;
  color: #155724;
  margin: 0;
}

@media (max-width: 1024px) {
  .text-column {
    width: 70% !important;
  }

  .comment-column {
    position: static;
    width: 70%;
    max-width: none;
    margin: 20px auto;
  }

  .comment-sticky {
    max-height: 300px;
  }
}

@media (max-width: 768px) {
  .text-column {
    width: 90% !important;
  }

  .comment-column {
    width: 90%;
  }

  .toggle-btn {
    padding: 6px 10px;
    font-size: 12px;
  }
}
</style>
