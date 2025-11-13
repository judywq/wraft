/**
 * useFileProcessor Composable
 *
 * Provides file processing functionality for extracting text from various file formats.
 * Currently supports:
 * - Microsoft Word documents (.docx)
 * - Plain text files (.txt)
 *
 * @returns {Object} Object containing processFile function and isProcessing reactive state
 */

import { ref } from 'vue'
import mammoth from 'mammoth'

// MIME type constants for supported file formats
const MIME_TYPE_DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
const MIME_TYPE_TXT = 'text/plain'

export function useFileProcessor() {
  /**
   * Reactive state: Indicates if a file is currently being processed
   */
  const isProcessing = ref(false)

  /**
   * Process a file and extract its text content
   *
   * Supported formats:
   * - .docx (Word documents) - Uses mammoth library to extract raw text
   * - .txt (Plain text) - Reads file as text directly
   *
   * @param file - The file to process
   * @returns {Promise<string>} The extracted text content
   * @throws {Error} If file type is not supported
   */
  const processFile = async (file: File): Promise<string> => {
    isProcessing.value = true
    try {
      if (file.type === MIME_TYPE_DOCX) {
        // Process Word document: convert to array buffer and extract text
        const arrayBuffer = await file.arrayBuffer()
        const result = await mammoth.extractRawText({ arrayBuffer })
        return result.value
      } else if (file.type === MIME_TYPE_TXT) {
        // Process plain text file: read directly as text
        const text = await file.text()
        return text
      } else {
        throw new Error(`Unsupported file type: ${file.type}. Supported types: .docx, .txt`)
      }
    } finally {
      // Always reset processing state, even if an error occurs
      isProcessing.value = false
    }
  }

  return {
    processFile,
    isProcessing,
  }
}
