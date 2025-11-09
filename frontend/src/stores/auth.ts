/**
 * Authentication Store
 *
 * Pinia store for managing user authentication state.
 * Features:
 * - Persistent state via localStorage
 * - User login/logout/signup operations
 * - Email verification
 * - Password management
 * - Automatic state restoration on app load
 *
 * @module stores/auth
 */

import { defineStore } from 'pinia';
import type { Router } from 'vue-router';
import { AuthService } from '@/services/authService';
import type { AuthState } from '@/types/auth';

export const useAuthStore = defineStore('auth', {
  /**
   * Initial state with localStorage persistence
   * Restores authentication state from localStorage if available
   */
  state: (): AuthState => {
    const storedState = localStorage.getItem('authState');
    return storedState ? JSON.parse(storedState) : {
      user: null,
      isAuthenticated: false,
      loading: false,
      error: null
    };
  },

  /**
   * Computed getters for derived state
   */
  getters: {
    /** Check if user is fully logged in (authenticated and has user data) */
    isLoggedIn: (state) => state.isAuthenticated && state.user !== null,

    /** Get current user object */
    currentUser: (state) => state.user,

    /** Check if any async operation is in progress */
    isLoading: (state) => state.loading,

    /** Check if there's an error in the store */
    hasError: (state) => state.error !== null
  },

  /**
   * Actions for authentication operations
   */
  actions: {
    /**
     * Set loading state
     * @param loading - Whether an async operation is in progress
     */
    setLoading(loading: boolean) {
      this.loading = loading;
    },

    /**
     * Set error state
     * @param error - Error message or null to clear error
     */
    setError(error: string | null) {
      this.error = error;
    },

    /**
     * Login user with email and password
     *
     * Authenticates user, updates store state, persists to localStorage,
     * and optionally redirects to home page.
     *
     * @param email - User's email address
     * @param password - User's password
     * @param router - Optional Vue Router instance for navigation
     * @throws Re-throws API errors for component-level handling
     */
    async login(email: string, password: string, router: Router | null = null) {
      this.setLoading(true);
      this.setError(null);

      try {
        const data = await AuthService.login(email, password);
        if (data.user) {
          this.user = data.user;
          this.isAuthenticated = true;
          this.saveState();

          if (router) {
            await router.push({ name: "home" });
          }
        }
      } catch (error: any) {
        // Clear state on login failure
        this.isAuthenticated = false;
        this.user = null;
        this.setError(error.message || 'Login failed');
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    /**
     * Logout current user
     *
     * Logs out user on server, clears local state, and optionally
     * redirects to login page. Clears state even if server logout fails.
     *
     * @param router - Optional Vue Router instance for navigation
     * @throws Re-throws API errors for component-level handling
     */
    async logout(router: Router | null = null) {
      this.setLoading(true);
      this.setError(null);

      try {
        await AuthService.logout();
        this.clearState();

        if (router) {
          await router.push({ name: "login" });
        }
      } catch (error: any) {
        // Even if logout fails on server, clear local state
        // This ensures user can't access protected pages with invalid session
        this.clearState();
        this.setError(error.message || 'Logout failed');
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    /**
     * Register a new user account
     *
     * Creates new user account and optionally redirects to email verification page.
     *
     * @param email - User's email address
     * @param password1 - User's password
     * @param password2 - Password confirmation
     * @param name - User's full name
     * @param router - Optional Vue Router instance for navigation
     * @throws Re-throws API errors for component-level handling
     */
    async signup(
      email: string,
      password1: string,
      password2: string,
      name: string,
      router?: Router
    ) {
      this.setLoading(true);
      this.setError(null);

      try {
        await AuthService.signup(email, password1, password2, name);
        if (router) {
          await router.push({ name: "verify-email" });
        }
      } catch (error: any) {
        this.setError(error.message || 'Registration failed');
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    /**
     * Verify user's email address
     *
     * Verifies email with key from verification email and optionally
     * redirects to login page on success.
     *
     * @param key - Email verification key
     * @param router - Optional Vue Router instance for navigation
     * @returns Promise resolving to API response
     * @throws Re-throws API errors for component-level handling
     */
    async verifyEmail(key: string, router: Router | null = null) {
      this.setLoading(true);
      this.setError(null);

      try {
        const response = await AuthService.verifyEmail(key);
        if (response?.status === 200) {
          if (router) {
            await router.push({ name: "login" });
          }
        }
        return response;
      } catch (error: any) {
        this.setError(error.message || 'Email verification failed');
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    /**
     * Fetch current user data from server
     *
     * Refreshes user data and updates authentication state.
     * Clears state if fetch fails (e.g., invalid session).
     *
     * @throws Re-throws API errors for component-level handling
     */
    async fetchUser() {
      this.setLoading(true);
      this.setError(null);

      try {
        const user = await AuthService.fetchUser();
        this.user = user;
        this.isAuthenticated = true;
        this.saveState();
      } catch (error: any) {
        // Clear state if user fetch fails (session may be invalid)
        this.clearState();
        this.setError(error.message || 'Failed to fetch user data');
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    /**
     * Persist authentication state to localStorage
     *
     * Saves user data and authentication status for state restoration
     * on app reload. Does not persist loading or error states.
     */
    saveState() {
      localStorage.setItem('authState', JSON.stringify({
        user: this.user,
        isAuthenticated: this.isAuthenticated,
        loading: false, // Never persist loading state
        error: null // Never persist error state
      }));
    },

    /**
     * Clear authentication state
     *
     * Resets all state to initial values and removes persisted data
     * from localStorage. Used on logout and authentication failures.
     */
    clearState() {
      this.user = null;
      this.isAuthenticated = false;
      this.error = null;
      localStorage.removeItem('authState');
    },

    /**
     * Initialize store on app startup
     *
     * Should be called when the app starts (e.g., in main.ts or App.vue).
     * If user appears to be authenticated (from localStorage), validates
     * the session by fetching user data from server.
     *
     * If fetch fails, clears state (session may be expired/invalid).
     */
    async initialize() {
      if (this.isAuthenticated) {
        try {
          await this.fetchUser();
        } catch (error) {
          // If fetching user fails, clear the state
          // This handles expired sessions gracefully
          this.clearState();
        }
      }
    }
  }
});
