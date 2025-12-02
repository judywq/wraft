<template>
  <div class="min-h-screen relative">
    <!-- Floating background elements -->
    <div class="floating-orbs">
      <div class="orb" v-for="n in 5" :key="n" :class="`orb-${n}`"></div>
    </div>

    <div class="main-container">
      <!-- Header Section - Centered -->
      <header class="hero-section">
        <div class="sage-avatar" :class="{ processing: isAnalyzing }">
          {{ isAnalyzing ? '🔮' : '🧙‍♂️' }}
        </div>
        <h1 class="main-title">WrAFT</h1>
        <p class="subtitle">Your AI writing mentor, ready to unlock your essay's potential</p>
      </header>

      <!-- Main Content Grid -->
      <div class="content-grid">
        <!-- Step 1: Topic Input -->
        <div class="step-card topic-card">
          <div class="step-badge">01</div>
          <div class="card-header">
            <h3>🎯 What's your focus?</h3>
            <p>Tell me about your essay topic</p>
          </div>
          <FormField v-slot="{ componentField }" name="essay_prompt">
            <FormItem>
              <FormControl>
                <Textarea
                  v-bind="componentField"
                  class="topic-input"
                  placeholder="Do you agree or disagree with the following statement? ..."
                  :disabled="isProcessing || isPending"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          </FormField>
        </div>

        <!-- Step 2: Essay Input -->
        <div class="step-card essay-card">
          <div class="step-badge">02</div>
          <div class="card-header">
            <h3>📝 Share your writing</h3>
            <p>Please use a newline character to separate paragraphs.</p>
            <div class="input-methods">
              <button
                :class="{ active: inputMethod === 'upload' }"
                @click="inputMethod = 'upload'"
                class="method-btn"
              >
                📄 Upload File
              </button>
              <button
                :class="{ active: inputMethod === 'paste' }"
                @click="inputMethod = 'paste'"
                class="method-btn"
              >
                ✏️ Paste Text
              </button>
            </div>
          </div>

          <!-- Upload Method -->
          <div v-if="inputMethod === 'upload'" class="upload-section">
            <div
              class="upload-zone"
              @click="fileInput?.click()"
              @dragover.prevent="dragActive = true"
              @dragleave.prevent="dragActive = false"
              @drop.prevent="handleFileDrop"
              :class="{ 'drag-active': dragActive }"
            >
              <div class="upload-icon">{{ dragActive ? '📥' : '📄' }}</div>
              <p>
                <strong>{{ dragActive ? 'Drop it here!' : 'Click to upload' }}</strong>
              </p>
              <p class="upload-hint">Word files (.docx) or text files (.txt)</p>
              <input
                ref="fileInput"
                type="file"
                style="display: none"
                accept=".docx,.txt"
                @change="handleFileUpload"
              />
            </div>
          </div>

          <!-- Paste Method -->
          <div v-if="inputMethod === 'paste'" class="paste-section">
            <FormField v-slot="{ componentField }" name="essay_text">
              <FormItem>
                <FormControl>
                  <Textarea
                    ref="essayTextarea"
                    v-bind="componentField"
                    class="essay-textarea"
                    :rows="10"
                    placeholder="Paste your essay text here..."
                    :disabled="isProcessing || isPending"
                  />
                </FormControl>
                <FormMessage />
                <div class="text-stats" v-if="form.values.essay_text">
                  <span>{{ wordCount }} words</span>
                  <span>{{ charCount }}/{{ MAX_CHARS }} characters</span>
                </div>
              </FormItem>
            </FormField>
          </div>
        </div>

        <!-- Step 3: Assessment Type -->
        <div class="step-card assessment-card">
          <div class="step-badge">03</div>
          <div class="assessment-content">
            <div class="assessment-info">
              <h3>🎯 Choose your assessment</h3>
              <p>Select what type of feedback you need</p>
            </div>

            <div class="assessment-options">
              <div
                class="assessment-option"
                :class="{ selected: assessmentType === 'score' }"
                @click="assessmentType = 'score'"
              >
                <div class="option-icon-large">📊</div>
                <div class="option-content">
                  <div class="option-title">Score</div>
                  <div class="option-description">Get a numerical grade with key metrics</div>
                </div>
              </div>

              <div
                class="assessment-option"
                :class="{ selected: assessmentType === 'feedback' }"
                @click="assessmentType = 'feedback'"
              >
                <div class="option-icon-large">💬</div>
                <div class="option-content">
                  <div class="option-title">Feedback</div>
                  <div class="option-description">Detailed comments and suggestions</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Floating Action Button -->
      <button
        class="fab-analyze"
        @click="handleSubmit"
        :disabled="!canAnalyze"
        :class="{ ready: canAnalyze, pulse: shouldPulse }"
        title="Start Analysis"
      >
        {{ isAnalyzing ? '⏳' : '🚀' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useFileProcessor } from '@/composables/useFileProcessor'
import { useToast } from '@/components/ui/toast/use-toast'
import { EssayService } from '@/services/writingService'
import type { EssayRequest } from '@/models/writing'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { FormControl, FormField, FormItem, FormMessage } from '@/components/ui/form'
import { essayFormSchema, MAX_CHARS } from '@/lib/schema'

// Router
const router = useRouter()

// Composables
const { toast } = useToast()
const { processFile, isProcessing } = useFileProcessor()

// Form setup
const form = useForm({
  validationSchema: toTypedSchema(essayFormSchema),
  initialValues: {
    essay_text: '',
    essay_prompt: '',
  },
})

// State - Input Method
const inputMethod = ref<'upload' | 'paste'>('paste')
const dragActive = ref(false)
const uploadedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const essayTextarea = ref<typeof Textarea | null>(null)

// State - Assessment
const assessmentType = ref<'score' | 'feedback'>('score')
const isAnalyzing = ref(false)
const generalError = ref('')
const isLoading = ref(false)

// State - Request tracking
const currentRequest = ref<EssayRequest | null>(null)
const pollingInterval = ref<ReturnType<typeof setInterval> | null>(null)

// Computed - Text statistics
const charCount = computed(() => form.values.essay_text?.length || 0)
const wordCount = computed(() => {
  return form.values.essay_text?.split(/\s+/).filter((word) => word.length > 0).length || 0
})
const isOverLimit = computed(() => charCount.value > MAX_CHARS)

// Computed - Request status
const isPending = computed(() => currentRequest.value?.status === 'PENDING')
const isCompleted = computed(() => currentRequest.value?.status === 'COMPLETED')
const isFailed = computed(() => currentRequest.value?.status === 'FAILED')

// Computed - UI state
const canAnalyze = computed(() => {
  return !!(
    form.values.essay_prompt?.trim() &&
    assessmentType.value &&
    ((inputMethod.value === 'paste' && form.values.essay_text?.trim()) ||
      (inputMethod.value === 'upload' && uploadedFile.value))
  )
})

const shouldPulse = computed(() => {
  return canAnalyze.value && !isAnalyzing.value
})

// Methods - File handling
const handleFileUpload = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) {
    uploadedFile.value = file
    await handleFileSelected(file)
  }
}

const handleFileDrop = async (event: DragEvent) => {
  dragActive.value = false
  const file = event.dataTransfer?.files[0]
  if (file) {
    uploadedFile.value = file
    await handleFileSelected(file)
  }
}

const handleFileSelected = async (file: File) => {
  generalError.value = ''
  isLoading.value = true

  try {
    const text = await processFile(file)
    if (text.length > MAX_CHARS) {
      toast({
        description: `The uploaded document exceeds ${MAX_CHARS} characters. Only the first ${MAX_CHARS} characters will be used.`,
        variant: 'destructive',
      })
      form.setFieldValue('essay_text', text.slice(0, MAX_CHARS))
    } else {
      form.setFieldValue('essay_text', text)
    }
  } catch (err) {
    toast({
      description: "Failed to process document. Please make sure it's a valid Word document.",
      variant: 'destructive',
    })
    console.error('Error processing document:', err)
  } finally {
    isLoading.value = false
  }
}

// Methods - Form submission
const handleSubmit = form.handleSubmit(async (values) => {
  generalError.value = ''
  isAnalyzing.value = true

  try {
    const response = await EssayService.submitEssay({
      essay_text: values.essay_text,
      essay_prompt: values.essay_prompt,
    })
    currentRequest.value = response

    const id = currentRequest.value?.id
    if (id) {
      router.push({ name: 'result', params: { id: id } })
    } else {
      toast({
        description: 'Failed to submit essay. Please try again.',
        variant: 'destructive',
      })
    }
  } catch (err: any) {
    if (err.fieldErrors) {
      form.setErrors(err.fieldErrors)
    }
    if (err.nonFieldError) {
      generalError.value = err.nonFieldError
    }
  } finally {
    isAnalyzing.value = false
  }
})

const handleReset = async () => {
  form.setFieldValue('essay_text', '')
  form.setFieldValue('essay_prompt', '')
  currentRequest.value = null
  generalError.value = ''

  // Focus the textarea after a short delay to ensure the DOM has updated
  setTimeout(() => {
    essayTextarea.value?.focus()
  }, 0)
}

// Lifecycle
onUnmounted(() => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
  }
})
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.floating-orbs {
  position: fixed;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.orb {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  animation: float 25s infinite ease-in-out;
}

.orb-1 {
  width: 100px;
  height: 100px;
  top: 15%;
  left: 8%;
  animation-delay: 0s;
}
.orb-2 {
  width: 60px;
  height: 60px;
  top: 70%;
  right: 20%;
  animation-delay: -8s;
}
.orb-3 {
  width: 80px;
  height: 80px;
  bottom: 20%;
  left: 15%;
  animation-delay: -15s;
}
.orb-4 {
  width: 120px;
  height: 120px;
  top: 40%;
  right: 10%;
  animation-delay: -5s;
}
.orb-5 {
  width: 40px;
  height: 40px;
  top: 60%;
  left: 50%;
  animation-delay: -12s;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0) rotate(0deg);
    opacity: 0.3;
  }
  25% {
    transform: translateY(-40px) rotate(90deg);
    opacity: 0.6;
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
    opacity: 0.4;
  }
  75% {
    transform: translateY(-60px) rotate(270deg);
    opacity: 0.7;
  }
}

.main-container {
  position: relative;
  z-index: 2;
  min-height: 100vh;
  display: grid;
  grid-template-areas:
    'header'
    'content';
  grid-template-columns: 1fr;
  grid-template-rows: auto 1fr;
  gap: 2rem;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.hero-section {
  grid-area: header;
  text-align: center;
  position: relative;
  padding: 2rem 0;
}

.user-profile {
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 25px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
}

.user-profile:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
}

.profile-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #74b9ff, #0984e3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1rem;
}

.profile-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.profile-name {
  font-weight: 600;
  font-size: 0.9rem;
}

.profile-level {
  font-size: 0.75rem;
  opacity: 0.8;
}

.sage-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ffeaa7, #fab1a0);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  margin: 0 auto 1rem;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.sage-avatar.processing {
  animation: spin 2s infinite linear;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.main-title {
  color: white;
  font-size: 3rem;
  font-weight: 200;
  margin-bottom: 0.5rem;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.2rem;
  font-weight: 300;
}

.content-grid {
  grid-area: content;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto auto;
  gap: 2rem;
  align-content: start;
  max-width: 1000px;
  margin: 0 auto;
}

.step-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  padding: 2rem;
  position: relative;
  transition: all 0.3s ease;
}

.step-card:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-5px);
}

.step-badge {
  position: absolute;
  top: -15px;
  left: 30px;
  background: linear-gradient(135deg, #ff6b6b, #ee5a24);
  color: white;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1rem;
  box-shadow: 0 5px 15px rgba(238, 90, 36, 0.4);
}

.topic-card {
  grid-column: 1;
  grid-row: 1 / 3;
}

.card-header h3 {
  color: white;
  font-size: 1.3rem;
  margin-bottom: 0.5rem;
}

.card-header p {
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 1.5rem;
}

.topic-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 15px;
  padding: 1rem;
  color: white;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s ease;
}

.topic-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.topic-input:focus {
  border-color: #74b9ff;
  background: rgba(255, 255, 255, 0.2);
}

.essay-card {
  grid-column: 2;
  grid-row: 1 / 3;
  display: flex;
  flex-direction: column;
}

.input-methods {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.method-btn {
  flex: 1;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 0.75rem;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.method-btn.active {
  background: rgba(116, 185, 255, 0.3);
  border-color: #74b9ff;
}

.method-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.upload-section,
.paste-section {
  flex: 1;
  margin-top: 1.5rem;
}

.upload-zone {
  border: 2px dashed rgba(255, 255, 255, 0.4);
  border-radius: 15px;
  padding: 3rem 1rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
}

.upload-zone:hover,
.upload-zone.drag-active {
  border-color: #74b9ff;
  background: rgba(116, 185, 255, 0.1);
}

.upload-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.upload-hint {
  opacity: 0.7;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.essay-textarea {
  width: 100%;
  min-height: 200px;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 15px;
  padding: 1rem;
  color: white;
  font-size: 1rem;
  outline: none;
  resize: vertical;
  font-family: inherit;
  line-height: 1.6;
}

.essay-textarea::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.essay-textarea:focus {
  border-color: #74b9ff;
  background: rgba(255, 255, 255, 0.15);
}

.text-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}

.assessment-card {
  grid-column: 1 / 3;
  grid-row: 3;
}

.assessment-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.assessment-info h3 {
  color: white;
  font-size: 1.3rem;
  margin-bottom: 0.5rem;
}

.assessment-info p {
  color: rgba(255, 255, 255, 0.8);
}

.assessment-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.assessment-option {
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 15px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.assessment-option:hover {
  background: rgba(255, 255, 255, 0.2);
}

.assessment-option.selected {
  background: rgba(116, 185, 255, 0.3);
  border-color: #74b9ff;
}

.option-icon-large {
  font-size: 2.5rem;
  flex-shrink: 0;
}

.option-content {
  flex: 1;
}

.option-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.option-description {
  font-size: 0.9rem;
  opacity: 0.8;
  line-height: 1.4;
}

.analysis-categories {
  margin-top: 1rem;
}

.analysis-categories h4 {
  color: white;
  font-size: 1rem;
  margin-bottom: 1rem;
}

.category-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.category-tag {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.category-tag:hover {
  background: rgba(255, 255, 255, 0.2);
}

.category-tag.selected {
  background: rgba(116, 185, 255, 0.3);
  border-color: #74b9ff;
}

.tag-icon {
  font-size: 1rem;
}

.tag-label {
  font-weight: 500;
}

.fab-analyze {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #00b894, #55a3ff);
  border: none;
  border-radius: 50%;
  color: white;
  font-size: 2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 10px 30px rgba(0, 184, 148, 0.4);
  z-index: 100;
}

.fab-analyze:hover {
  transform: scale(1.1);
  box-shadow: 0 15px 40px rgba(0, 184, 148, 0.6);
}

.fab-analyze.pulse {
  animation: pulse 2s infinite;
}

.fab-analyze:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: scale(0.9);
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}
</style>
