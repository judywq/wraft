/**
 * Validation Schemas
 *
 * A centralized collection of Zod-based validation rules for form fields and form submissions.
 * Designed for consistent validation logic across authentication, essay, and profile forms.
 *
 * @module validations
 */

import { z } from 'zod'

// ============================================================================
// Shared Constants
// ============================================================================

/**
 * Defines maximum character length for essay-related text inputs.
 * Helps prevent overly long submissions that may affect performance.
 */
export const MAX_CHARS = 5000

// ============================================================================
// Core Field Validators
// ============================================================================

/**
 * Name validation rule
 * - Cannot be empty
 * - Limited to 255 characters (due to DB constraint)
 */
export const nameSchema = z.string()
  .min(1, 'Name field cannot be blank')
  .max(255, 'Name must be 255 characters or fewer')

/**
 * Email validation rule
 * - Field is mandatory
 * - Must follow valid email format
 */
export const emailSchema = z.string()
  .min(1, 'Email address is required')
  .email('Please provide a valid email format')

/**
 * Password validation rule
 * - At least 8 characters long
 * - Must include uppercase, lowercase, and numeric characters
 */
export const passwordSchema = z.string()
  .min(8, 'Password must contain at least 8 characters')
  .regex(/[a-z]/, 'Password must include a lowercase letter')
  .regex(/\d/, 'Password must include at least one number')

// ============================================================================
// Authentication & Account Form Schemas
// ============================================================================

/**
 * Login form schema
 * Uses simplified password validation compared to sign-up.
 */
export const loginFormSchema = z.object({
  email: emailSchema,
  password: z.string()
    .min(8, 'Password should have a minimum of 8 characters')
})

/**
 * Signup form schema
 * Ensures both password fields match before submission.
 */
export const signupFormSchema = z.object({
  name: nameSchema,
  email: emailSchema,
  password1: passwordSchema,
  password2: z.string().min(1, 'Please re-enter your password'),
}).refine((data) => data.password1 === data.password2, {
  message: 'Passwords do not match',
  path: ['password2'],
})

/**
 * Update password form schema
 * Requires old password and confirmation for new one.
 */
export const updatePasswordFormSchema = z.object({
  old_password: z.string().min(1, 'Please enter your current password'),
  new_password1: passwordSchema,
  new_password2: z.string().min(1, 'Please confirm your new password'),
}).refine((data) => data.new_password1 === data.new_password2, {
  message: 'Passwords do not match',
  path: ['new_password2'],
})

/**
 * Set new password form schema
 * Used when resetting password through a reset email link.
 */
export const setNewPasswordFormSchema = z.object({
  new_password1: passwordSchema,
  new_password2: z.string().min(1, 'Please confirm your new password'),
}).refine((data) => data.new_password1 === data.new_password2, {
  message: 'Passwords do not match',
  path: ['new_password2'],
})

/**
 * Request password reset form schema
 * Validates only the email for sending password reset link.
 */
export const requestPasswordResetFormSchema = z.object({
  email: emailSchema,
})

/**
 * Email verification form schema
 * Ensures the verification code field is not left blank.
 */
export const verifyEmailFormSchema = z.object({
  verificationCode: z.string().min(1, 'Verification code is required'),
})

// ============================================================================
// Essay Submission Schemas
// ============================================================================

/**
 * Essay form schema
 * Validates essay content and prompt fields with character limits.
 */
export const essayFormSchema = z.object({
  essay_prompt: z.string()
    .min(1, 'Please enter your essay topic')
    .max(MAX_CHARS, `Topic must be within ${MAX_CHARS} characters`),
  essay_text: z.string()
    .min(1, 'Please write your essay before submitting')
    .max(MAX_CHARS, `Essay must be within ${MAX_CHARS} characters`),
})
