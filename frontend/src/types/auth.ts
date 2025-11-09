/**
 * Type Definitions for Authentication
 *
 * @module types/auth
 */

/**
 * User data structure
 *
 * Represents an authenticated user in the system.
 * Matches the user object returned by django-rest-auth.
 */
export interface User {
  /** Primary key (user ID) */
  pk: number;

  /** Username */
  username: string;

  /** Email address */
  email: string;

  /** First name (optional) */
  first_name: string | null;

  /** Last name (optional) */
  last_name: string | null;
}

/**
 * Authentication store state
 *
 * Complete state structure for the Pinia authentication store.
 * Includes user data, authentication status, loading state, and errors.
 */
export interface AuthState {
  /** Current authenticated user (null if not authenticated) */
  user: User | null;

  /** Whether user is currently authenticated */
  isAuthenticated: boolean;

  /** Whether an async authentication operation is in progress */
  loading: boolean;

  /** Current error message (null if no error) */
  error: string | null;
}
