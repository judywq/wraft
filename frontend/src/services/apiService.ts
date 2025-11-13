/**
 * API Service
 *
 * Centralized Axios instance configuration for all API requests.
 * Features:
 * - CSRF token handling (with secure cookie support for HTTPS)
 * - Request/response interceptors
 * - Error handling and transformation
 * - Automatic authentication error handling (403 responses)
 *
 * @module api
 */

import axios from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import Cookies from 'js-cookie';
import { useAuthStore } from '@/stores/auth';
import router from '@/router';
import { AxiosError } from 'axios';

// ============================================================================
// Configuration
// ============================================================================

/**
 * API base URL from environment variables
 * Set via VITE_API_BASE_URL in .env file
 */
const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL;
console.debug('api.ts initialization - API_BASE_URL:', { API_BASE_URL });

/**
 * CSRF token cookie key
 * Uses secure cookie name for HTTPS connections (browser security requirement)
 */
let csrf_key = 'csrftoken';
if (window.location.protocol === 'https:') {
  // Secure cookies required for HTTPS to prevent XSS attacks
  csrf_key = '__Secure-csrftoken';
}

/**
 * Axios instance with base configuration
 * - Base URL from environment
 * - Credentials included for cookie-based auth
 * - 5 second timeout
 * - JSON content type
 */
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Required for CSRF cookies
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// Request Interceptor
// ============================================================================

/**
 * Request Interceptor: Add CSRF token to all requests
 *
 * Automatically retrieves CSRF token from cookies and adds it to request headers.
 * Required for Django REST Framework CSRF protection.
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    const csrfToken = Cookies.get(csrf_key);
    if (csrfToken && config.headers) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    return config;
  },
  (error: any) => Promise.reject(error)
);

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * API error response structure from Django REST Framework
 * Can contain field-specific errors or general error messages
 */
export interface ApiErrorResponse {
  non_field_errors?: string[];
  detail?: string | string[];
  error?: string | string[];
  [key: string]: any; // Field-specific errors
}

/**
 * Standardized error object for application use
 * Transforms API errors into a consistent format
 */
export interface ApiError {
  message: string; // Primary error message
  code: string; // HTTP status code or error type
  fieldErrors?: Record<string, string>; // Field-specific validation errors
  nonFieldError?: string; // General error message
}

// ============================================================================
// Error Handling
// ============================================================================

/**
 * Transform Axios errors into standardized ApiError format
 *
 * Handles three types of errors:
 * 1. Server response errors (4xx, 5xx) - extracts field and non-field errors
 * 2. Network errors (no response) - connection/timeout issues
 * 3. Request errors (request setup failed) - configuration issues
 *
 * @param error - Axios error with potential API error response
 * @returns Standardized ApiError object
 */
function handleApiError(error: AxiosError<ApiErrorResponse>): ApiError {
  // Server responded with error status (4xx, 5xx)
  if (error.response) {
    const { data } = error.response;
    const fieldErrors: Record<string, string> = {};
    let nonFieldError: string | undefined;

    // Keys that indicate general/non-field errors
    const nonFieldErrorKeys = [
      'non_field_errors',
      'detail',
      'error'
    ];

    // Process all error fields
    Object.entries(data).forEach(([key, value]) => {
      if (nonFieldErrorKeys.includes(key)) {
        // Handle general errors (can be string or array)
        if (Array.isArray(value)) {
          nonFieldError = value[0];
        } else {
          nonFieldError = value;
        }
      } else {
        // Handle field-specific validation errors
        if (Array.isArray(value)) {
          fieldErrors[key] = value[0]; // Take first error message
        } else {
          fieldErrors[key] = value;
        }
      }
    });

    return {
      message: nonFieldError || 'An error occurred',
      code: error.response.status.toString(),
      fieldErrors: Object.keys(fieldErrors).length > 0 ? fieldErrors : undefined,
      nonFieldError
    };
  }

  // Network error: request made but no response received
  if (error.request) {
    return {
      message: 'No response from server',
      code: 'NETWORK_ERROR',
      nonFieldError: 'Network error. Please try again.'
    };
  }

  // Request setup error: request was never sent
  return {
    message: error.message || 'An unexpected error occurred',
    code: 'REQUEST_ERROR',
    nonFieldError: 'An unexpected error occurred. Please try again.'
  };
}

// ============================================================================
// Response Interceptor
// ============================================================================

/**
 * Response Interceptor: Handle authentication errors and transform errors
 *
 * - Catches 403 Forbidden errors due to missing/invalid credentials
 * - Automatically logs out user and redirects to login
 * - Transforms all errors to standardized ApiError format
 */
api.interceptors.response.use(
  response => response,
  async error => {
    // Handle 403 Forbidden (authentication/authorization errors)
    if (error.response && error.response.status === 403) {
      const { detail } = error.response.data;

      // Check if error is due to missing/invalid authentication credentials
      // Server returns messages like "Authentication credentials were not provided."
      if (detail && typeof detail === 'string' && detail.includes('credentials')) {
        const authStore = useAuthStore();
        await authStore.logout();
        router.push({ name: 'login' });
      }
    }

    // Transform error to standardized format and re-throw
    throw handleApiError(error);
  }
);

export default api;
