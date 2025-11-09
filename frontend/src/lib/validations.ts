/**
 * Validation Schemas
 *
 * Centralized Zod validation schemas for form validation across the application.
 * Provides reusable validation rules for common form fields and complete form schemas.
 *
 * @module validations
 */

import { z } from 'zod'

// ============================================================================
// Basic Field Validations
// ============================================================================

/**
 * Email validation schema
 * - Required field
 * - Must be a valid email format
 */
export const emailSchema = z.string()
  .min(1, 'Email is required')
  .email('Invalid email address')

/**
 * Password validation schema
 * - Minimum 8 characters
 * - At least one uppercase letter
 * - At least one lowercase letter
 * - At least one number
 */
export const passwordSchema = z.string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/\d/, 'Password must contain at least one number')

/**
 * Name validation schema
 * - Required field
 * - Maximum 255 characters (database constraint)
 */
export const nameSchema = z.string()
  .min(1, 'Name is required')
  .max(255, 'Name cannot exceed 255 characters')

// ============================================================================
// Authentication Form Schemas
// ============================================================================

/**
 * Login form validation schema
 * Uses simplified password validation (no regex checks) for login
 */
export const loginFormSchema = z.object({
  email: emailSchema,
  password: z.string().min(8, 'Password must be at least 8 characters')
    .regex(/\d/, 'Password must contain at least one number'),
})

/**
 * Signup form validation schema
 * Includes password confirmation matching validation
 */
export const signupFormSchema = z.object({
  name: nameSchema,
  email: emailSchema,
  password1: passwordSchema,
  password2: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.password1 === data.password2, {
  message: "Passwords don't match",
  path: ["password2"], // Error appears on password2 field
})

/**
 * Password reset form validation schema
 * Used when user resets password via email link
 */
export const resetPasswordFormSchema = z.object({
  new_password1: passwordSchema,
  new_password2: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.new_password1 === data.new_password2, {
  message: "Passwords don't match",
  path: ["new_password2"],
})

/**
 * Change password form validation schema
 * Used when user changes password from account settings
 * Requires old password for security
 */
export const changePasswordFormSchema = z.object({
  old_password: z.string().min(1, 'Current password is required'),
  new_password1: passwordSchema,
  new_password2: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.new_password1 === data.new_password2, {
  message: "Passwords don't match",
  path: ["new_password2"],
})

/**
 * Forgot password form validation schema
 * Only requires email to send reset link
 */
export const forgotPasswordFormSchema = z.object({
  email: emailSchema,
})

/**
 * Email verification form validation schema
 * Used to verify email with code sent to user
 */
export const verifyEmailFormSchema = z.object({
  verificationCode: z.string().min(1, 'Verification code is required'),
})

// ============================================================================
// Essay Form Schemas
// ============================================================================

/**
 * Maximum character limit for essay text and prompts
 * Prevents excessive input that could cause performance issues
 */
export const MAX_CHARS = 5000

/**
 * Essay submission form validation schema
 * Validates both essay text and essay prompt/topic
 * Both fields are required and have character limits
 */
export const essayFormSchema = z.object({
  essay_text: z.string()
    .min(1, 'Please enter your essay')
    .max(MAX_CHARS, `Text cannot exceed ${MAX_CHARS} characters`),
  essay_prompt: z.string()
    .min(1, 'Please enter the essay topic')
    .max(MAX_CHARS, `Topic cannot exceed ${MAX_CHARS} characters`),
})
