<template>
  <div class="view-content">
    <!-- Loading state for comments -->
    <div v-if="!hasDeepComments" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading deep feedback...</p>
    </div>

    <div v-else class="content-layout">
      <!-- Left column for paragraph comments -->
      <div class="paragraph-comments-column">
        <div class="paragraph-comments-container" id="paragraph-comments-container">
          <div
            v-for="(comment, index) in macro_comments"
            :key="index"
            class="paragraph-comment"
            :data-target="`paragraph-${index}`"
            @mouseenter="handleParagraphCommentHover(index, true)"
            @mouseleave="handleParagraphCommentHover(index, false)"
          >
            <div class="paragraph-comment-header">Paragraph {{ index + 1 }}</div>
            <div class="paragraph-comment-text">{{ comment.comment }}</div>
          </div>
        </div>
      </div>

      <!-- Middle column for the text -->
      <div class="text-column">
        <div class="text-container" id="deep-text-container">
          <div
            v-for="(paragraph, index) in paragraphs"
            :key="index"
            :id="`paragraph-${index}`"
            class="text-paragraph"
            :class="{ 'active-paragraph': activeParagraph === index }"
            @mouseenter="handleParagraphHover(index, true)"
            @mouseleave="handleParagraphHover(index, false)"
          >
            <template v-for="(segment, segIndex) in getParagraphSegments(paragraph, index)">
              <span
                v-if="segment.comments.length > 0"
                class="text-segment highlighted"
                :class="{ active: isSegmentActive(segment) }"
                :style="{ backgroundColor: getSegmentBackgroundColor(segment) }"
                :data-comments="JSON.stringify(segment.comments)"
                :data-comment-type="segment.commentType"
                @mouseenter="handleDeepMouseEnter"
                @mouseleave="handleDeepMouseLeave"
                @click="handleDeepClick"
                :key="`seg-${index}-${segIndex}-highlighted`"
              >
                {{ segment.text }}
              </span>
              <span v-else class="text-segment" :key="`seg-${index}-${segIndex}-normal`">
                {{ segment.text }}
              </span>
              <span
                v-if="segIndex < getParagraphSegments(paragraph, index).length - 1"
                :key="`space-${index}-${segIndex}`"
                >&nbsp;</span
              >
            </template>
          </div>
        </div>
      </div>

      <!-- Right column for inline comments -->
      <div class="inline-comments-column">
        <div class="comment-sticky" id="deep-comment-container">
          <!-- Loading state for micro comments -->
          <div v-if="!hasMicroComments" class="loading-container small-loading">
            <div class="loading-spinner small-spinner"></div>
            <p>Loading comments...</p>
          </div>
          <!-- Message when comments are loaded but none are active -->
          <div v-else-if="!activeComments.length" class="no-comment-message">
            Hover over highlighted text to view comments
          </div>
          <!-- Display active comments -->
          <template v-else>
            <div v-for="comment in activeComments" :key="comment.id" class="comment-item">
              <div
                class="comment-type"
                :style="{ backgroundColor: getCommentTypeColor(comment.type) }"
              >
                {{ comment.type.charAt(0).toUpperCase() + comment.type.slice(1) }}
              </div>
              <div class="highlighted-text">"{{ comment.highlighted_text }}"</div>
              <div class="comment-data">{{ comment.comment }}</div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { EssayEvaluationData } from '@/models/writing'
import { PARAGRAPH_DELIMITER } from '@/lib/utils'

const props = defineProps<{
  evaluationData: EssayEvaluationData
}>()

const activeParagraph = ref<number | null>(null)
const activeComments = ref<any[]>([])
const isDeepLocked = ref(false)

const paragraphs = computed(() => {
  return props.evaluationData.essay_text_corrected?.split(PARAGRAPH_DELIMITER)
})

const macro_comments = computed(() => {
  return props.evaluationData.deep.macro_comments || []
})

// Computed property to check if deep comments exist
const hasDeepComments = computed(() => {
  const deepData = props.evaluationData?.deep
  const hasMacro = deepData?.macro_comments && deepData.macro_comments.length > 0
  const hasMicro = deepData?.micro_comments && deepData.micro_comments.length > 0
  return hasMacro || hasMicro
})

// Computed property specifically for micro comments
const hasMicroComments = computed(() => {
  return (
    props.evaluationData?.deep?.micro_comments &&
    props.evaluationData.deep.micro_comments.length > 0
  )
})

const commentTypeColors = {
  clarity: 'rgba(65, 105, 225, 0.2)',
  formality: 'rgba(46, 139, 87, 0.2)',
  coherence: 'rgba(255, 140, 0, 0.2)',
  grammar: 'rgba(220, 20, 60, 0.2)',
  default: 'rgba(135, 206, 250, 0.2)',
}

const commentTypeActiveColors = {
  clarity: 'rgba(65, 105, 225, 0.4)',
  formality: 'rgba(46, 139, 87, 0.4)',
  coherence: 'rgba(255, 140, 0, 0.4)',
  grammar: 'rgba(220, 20, 60, 0.4)',
  default: 'rgba(65, 105, 225, 0.3)',
}

function getParagraphSegments(paragraphText: string, paragraphIndex: number) {
  if (!props.evaluationData.deep.micro_comments) {
    return [{ text: paragraphText, comments: [], commentType: 'default' }]
  }

  const micro_comments = props.evaluationData.deep.micro_comments.filter(
    (comment) => comment.paragraph_id === paragraphIndex,
  )

  if (micro_comments.length === 0) {
    return [{ text: paragraphText, comments: [], commentType: 'default' }]
  }

  const wordCount = paragraphText.trim().split(/\s+/).length
  const breaks = new Set([0, wordCount])

  micro_comments.forEach((comment) => {
    if (comment.start !== undefined && comment.end !== undefined) {
      breaks.add(comment.start)
      breaks.add(comment.end)
    }
  })

  const sortedBreaks = Array.from(breaks).sort((a, b) => a - b)
  const segments = []

  for (let i = 0; i < sortedBreaks.length - 1; i++) {
    const start = sortedBreaks[i]
    const end = sortedBreaks[i + 1]
    if (start === undefined || end === undefined) continue
    const text = wordSubstring(paragraphText, start, end)

    const segmentComments = micro_comments.filter(
      (comment) =>
        comment.start !== undefined &&
        comment.end !== undefined &&
        comment.start <= start &&
        comment.end >= end,
    )

    segments.push({
      text,
      start,
      end,
      comments: segmentComments,
      commentType:
        segmentComments.length > 0 && segmentComments[0] ? segmentComments[0].type : 'default',
    })
  }

  return segments
}

function wordSubstring(text: string, startWordIndex: number, endWordIndex: number) {
  const words = text.split(/\s+/)
  const selectedWords = words.slice(startWordIndex, endWordIndex)
  return selectedWords.join(' ')
}

function getCommentTypeColor(type: string) {
  return commentTypeColors[type as keyof typeof commentTypeColors] || commentTypeColors.default
}

function getSegmentBackgroundColor(segment: any) {
  const type = segment.commentType
  return isSegmentActive(segment)
    ? commentTypeActiveColors[type as keyof typeof commentTypeActiveColors] ||
        commentTypeActiveColors.default
    : commentTypeColors[type as keyof typeof commentTypeColors] || commentTypeColors.default
}

function isSegmentActive(segment: any) {
  return segment.comments.some((comment: any) =>
    activeComments.value.some((activeComment) => activeComment.id === comment.id),
  )
}

function handleParagraphCommentHover(index: number, isEnter: boolean) {
  if (isEnter) {
    activeParagraph.value = index
  } else {
    activeParagraph.value = null
  }
}

function handleParagraphHover(index: number, isEnter: boolean) {
  if (isEnter) {
    activeParagraph.value = index
  } else {
    activeParagraph.value = null
  }
}

function handleDeepClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  const comments = JSON.parse(target.dataset.comments || '[]')
  const commentType = target.dataset.commentType || 'default'

  if (comments.length > 0) {
    if (isDeepLocked.value) {
      const currentIds = comments.map((comment: any) => comment.id)
      const allCurrentActive = currentIds.every((id: string) =>
        activeComments.value.some((comment) => comment.id === id),
      )
      const onlyCurrentActive =
        activeComments.value.length === currentIds.length && allCurrentActive

      if (onlyCurrentActive) {
        isDeepLocked.value = false
        activeComments.value = []
        return
      }
    }

    activeComments.value = comments
    isDeepLocked.value = true
  }
}

function handleDeepMouseEnter(event: MouseEvent) {
  const target = event.target as HTMLElement
  const comments = JSON.parse(target.dataset.comments || '[]')
  const commentType = target.dataset.commentType || 'default'

  if (comments.length > 0 && !isDeepLocked.value) {
    activeComments.value = comments
    target.style.backgroundColor =
      commentTypeActiveColors[commentType as keyof typeof commentTypeActiveColors] ||
      commentTypeActiveColors.default
  }
}

function handleDeepMouseLeave(event: MouseEvent) {
  const target = event.target as HTMLElement
  const commentType = target.dataset.commentType || 'default'

  target.style.backgroundColor =
    commentTypeColors[commentType as keyof typeof commentTypeColors] || commentTypeColors.default

  if (!isDeepLocked.value) {
    activeComments.value = []
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
}

.text-container {
  color: var(--primary-color);
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  line-height: 1.8;
}

.paragraph-comments-column {
  position: absolute;
  top: 0px;
  left: 2%;
  width: 18%;
  max-width: 300px;
  z-index: 100;
  height: auto;
}

.paragraph-comments-container {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  padding: 15px;
  height: 100%;
  max-height: 400px;
}

.inline-comments-column {
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

.paragraph-comment {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 15px;
  margin-bottom: 20px;
  position: relative;
  transition: border-left 0.2s ease;
  border-left: 3px solid transparent;
}

.paragraph-comment::after {
  content: '';
  position: absolute;
  right: -15px;
  top: 50%;
  width: 15px;
  height: 2px;
  background-color: var(--connector-color);
}

.paragraph-comment-header {
  font-weight: bold;
  color: var(--primary-color);
  margin-bottom: 8px;
  padding-bottom: 5px;
  border-bottom: 1px solid var(--border-color);
}

.text-paragraph {
  position: relative;
  padding: 10px 0;
  margin-bottom: 20px;
  border-left: 3px solid transparent;
}

.text-paragraph.active-paragraph {
  border-left: 3px solid var(--primary-color);
}

.text-segment {
  position: relative;
  transition: background-color 0.2s;
}

.text-segment.highlighted {
  border-radius: 2px;
  cursor: pointer;
}

.text-segment.active {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.comment-type {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
  color: #333;
}

.highlighted-text {
  font-weight: bold;
  margin-bottom: 8px;
  color: var(--primary-color);
  font-style: italic;
}

.paragraph-comment-text {
  color: var(--primary-color);
  font-size: 14px;
  line-height: 1.6;
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

.comment-data {
  font-size: 14px;
  color: #4a5568;
  line-height: 1.6;
  word-wrap: break-word;
}

@media (max-width: 1200px) {
  .paragraph-comments-column,
  .inline-comments-column {
    position: absolute;
    max-height: 400px;
  }

  .paragraph-comments-column {
    top: 250px;
    left: 5%;
  }

  .inline-comments-column {
    top: 250px;
    right: 5%;
  }
}

@media (max-width: 1024px) {
  .text-column {
    width: 70% !important;
  }

  .paragraph-comments-column,
  .inline-comments-column {
    position: static;
    width: 70%;
    max-width: none;
    margin: 20px auto;
  }

  .paragraph-comments-container,
  .comment-sticky {
    max-height: 300px;
  }

  .paragraph-comment::after {
    display: none;
  }
}

@media (max-width: 768px) {
  .text-column {
    width: 90% !important;
  }

  .paragraph-comments-column,
  .inline-comments-column {
    width: 90%;
  }
}

/* Add styles for the new loading container */
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

/* Styles for the smaller loading container in the comment column */
.small-loading {
  padding: 20px 0; /* Reduced padding */
}

.small-spinner {
  width: 24px; /* Smaller spinner */
  height: 24px;
  border-width: 3px; /* Thinner border */
  margin-bottom: 10px;
}
</style>
