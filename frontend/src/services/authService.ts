/**
 * Authentication Service
 *
 * Service class for user authentication and account management API operations.
 * Handles login, signup, password management, and email verification.
 * Uses django-rest-auth endpoints.
 *
 * @class AuthService
 */

import api from '@/services/apiService'
import type { AxiosResponse } from 'axios'

/**
 * Login response structure
 * Contains user data and optional token (if token-based auth is used)
 */
interface LoginResponse {
  user: any
  token?: string
}

export class AuthService {
  /**
   * Authenticate user with email and password
   *
   * @param email - User's email address
   * @param password - User's password
   * @returns Promise resolving to LoginResponse with user data
   */
  public static async login(email: string, password: string): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/dj-rest-auth/login/', {
      email,
      password,
    })
    return response.data
  }

  /**
   * Logout current user
   * Invalidates session on server side
   *
   * @returns Promise that resolves when logout is complete
   */
  public static async logout(): Promise<void> {
    await api.post('/dj-rest-auth/logout/')
  }

  /**
   * Register a new user account
   *
   * @param email - User's email address
   * @param password1 - User's password
   * @param password2 - Password confirmation (must match password1)
   * @param name - User's full name
   * @returns Promise that resolves when registration is complete
   */
  public static async signup(
    email: string,
    password1: string,
    password2: string,
    name: string,
  ): Promise<void> {
    await api.post('/dj-rest-auth/registration/', {
      email,
      password1,
      password2,
      name,
    })
  }

  /**
   * Verify user's email address with verification key
   *
   * @param key - Email verification key sent to user's email
   * @returns Promise resolving to AxiosResponse
   */
  public static async verifyEmail(key: string): Promise<AxiosResponse> {
    const response = await api.post('/dj-rest-auth/registration/verify-email/', { key })
    return response
  }

  /**
   * Request password reset email
   *
   * Sends password reset link to user's email address.
   *
   * @param email - User's email address
   * @returns Promise resolving to AxiosResponse
   */
  public static async passwordReset(email: string): Promise<AxiosResponse> {
    const response = await api.post('/dj-rest-auth/password/reset/', { email })
    return response
  }

  /**
   * Confirm password reset with token from email
   *
   * Completes password reset process using UID and token from reset email.
   *
   * @param uid - User ID from reset link
   * @param token - Reset token from reset link
   * @param new_password1 - New password
   * @param new_password2 - New password confirmation
   * @returns Promise resolving to AxiosResponse
   */
  public static async passwordResetConfirm(
    uid: string,
    token: string,
    new_password1: string,
    new_password2: string
  ): Promise<AxiosResponse> {
    const response = await api.post('/dj-rest-auth/password/reset/confirm/', {
      uid,
      token,
      new_password1,
      new_password2
    })
    return response
  }

  /**
   * Fetch current authenticated user's data
   *
   * @returns Promise resolving to user object
   */
  public static async fetchUser(): Promise<any> {
    const response = await api.get('/dj-rest-auth/user/')
    return response.data
  }

  /**
   * Change user's password (authenticated users only)
   *
   * Requires current password for security.
   *
   * @param old_password - User's current password
   * @param new_password1 - New password
   * @param new_password2 - New password confirmation
   * @returns Promise resolving to AxiosResponse
   */
  public static async changePassword(
    old_password: string,
    new_password1: string,
    new_password2: string
  ): Promise<AxiosResponse> {
    const response = await api.post('/dj-rest-auth/password/change/', {
      old_password,
      new_password1,
      new_password2,
    })
    return response
  }
}
