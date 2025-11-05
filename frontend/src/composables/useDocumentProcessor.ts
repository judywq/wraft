import { ref } from 'vue'
import mammoth from 'mammoth'

export function useDocumentProcessor() {
  const isProcessing = ref(false)

  const processDocument = async (file: File): Promise<string> => {
    isProcessing.value = true
    try {
      if (file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
        const arrayBuffer = await file.arrayBuffer()
        const result = await mammoth.extractRawText({ arrayBuffer })
        return result.value
      } else if (file.type == 'text/plain') {
        const text = await file.text()
        return text
      } else {
        throw new Error('Invalid file type')
      }
    } finally {
      isProcessing.value = false
    }
  }

  return {
    processDocument,
    isProcessing,
  }
}
