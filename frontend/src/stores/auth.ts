/**
 * Auth Store (Pinia)
 *
 * Manages session state, persistence, and common auth flows.
 * This refactor keeps the same public API and AuthService method names:
 * - Actions: setLoading, setError, saveState, clearState, login, logout, signup, verifyEmail, fetchUser, initialize
 * - External calls: AuthService.login, AuthService.logout, AuthService.signup, AuthService.verifyEmail, AuthService.fetchUser
 *
 * The internals have been reorganized for clarity and single-responsibility.
 */

import { defineStore } from 'pinia';
import type { Router } from 'vue-router';
import { AuthService } from '@/services/authService';
import type { AuthState } from '@/models/auth';

// ---------------------------------------------------------------------------
// Constants & Pure Helpers
// ---------------------------------------------------------------------------

const PERSIST_KEY = 'authState';

/** Avoids throwing on malformed JSON */
function parseMaybe<T>(raw: string | null): T | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

/** Fresh state factory (no side effects) */
function newState(): AuthState {
  return {
    user: null,
    isAuthenticated: false,
    loading: false,
    error: null,
  };
}

/** Load state skeleton from localStorage (ignore transient flags) */
function loadPersisted(): AuthState {
  const persisted = parseMaybe<AuthState>(localStorage.getItem(PERSIST_KEY));
  if (!persisted) return newState();
  return {
    user: persisted.user ?? null,
    isAuthenticated: !!persisted.user && !!persisted.isAuthenticated,
    loading: false,
    error: null,
  };
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useAuthStore = defineStore('auth', {
  // State is hydrated from persistence
  state: (): AuthState => loadPersisted(),

  // Derived flags and quick accessors
  getters: {
    /** True when we have both a session and a user object */
    isLoggedIn(s): boolean {
      return !!s.isAuthenticated && !!s.user;
    },
    /** Current user object or null */
    currentUser(s) {
      return s.user;
    },
    /** Loading flag for UI */
    isLoading(s): boolean {
      return !!s.loading;
    },
    /** Error message for UI (nullable) */
    hasError(s): string | null {
      return s.error;
    },
  },

  actions: {
    // -----------------------------------------------------------------------
    // Internal helpers (private-by-convention)
    // -----------------------------------------------------------------------

    /** Single write-path to localStorage (never persist transient flags) */
    _persist() {
      const snapshot = {
        user: this.user,
        isAuthenticated: this.isAuthenticated,
        loading: false,
        error: null,
      };
      localStorage.setItem(PERSIST_KEY, JSON.stringify(snapshot));
    },

    /** Centralized reset for all state + persistence */
    _wipe() {
      const base = newState();
      this.user = base.user;
      this.isAuthenticated = base.isAuthenticated;
      this.loading = base.loading;
      this.error = base.error;
      localStorage.removeItem(PERSIST_KEY);
    },

    /** Convenience: start/stop a busy state and optionally clear error */
    _busy(on: boolean, clearErr = true) {
      this.loading = on;
      if (clearErr) this.error = null;
    },

    /** Fail with consistent UI state and throw for caller awareness */
    _die(err: unknown, fallback = 'Authentication error') {
      const msg =
        (typeof err === 'object' && err && 'message' in err && typeof (err as any).message === 'string')
          ? (err as any).message
          : fallback;
      this.loading = false;
      this.error = msg;
      throw err;
    },

    // -----------------------------------------------------------------------
    // Public API (names and signatures preserved)
    // -----------------------------------------------------------------------

    /**
     * Manually toggle the loading state.
     * Kept for compatibility with existing code that may flip this directly.
     */
    setLoading(value: boolean) {
      this.loading = value;
    },

    /**
     * Set or clear the error message (UI convenience).
     */
    setError(message: string | null) {
      this.error = message;
    },

    /**
     * Persist the current (non-transient) state.
     * Public method retained for compatibility (internal calls use _persist()).
     */
    saveState() {
      this._persist();
    },

    /**
     * Hard reset of the auth store and persistence.
     * Public method retained for compatibility (internal calls use _wipe()).
     */
    clearState() {
      this._wipe();
    },

    /**
     * Login with email/password. Optionally navigate after success.
     * Uses: AuthService.login
     */
    async login(email: string, password: string, router?: Router, redirectName?: string) {
      this._busy(true);
      try {
        const data = await AuthService.login(email, password);
        // Expecting { user: ... } shape; adjust only if your service differs
        this.user = data?.user ?? null;
        this.isAuthenticated = !!this.user;
        this._persist();

        if (router && this.isAuthenticated) {
          // If redirectName provided, route by name; otherwise go home
          if (redirectName) {
            await router.push({ name: redirectName });
          } else {
            await router.push({ name: 'home' });
          }
        }
        this._busy(false);
      } catch (e) {
        this._die(e);
      }
    },

    /**
     * Logout and clear state. Optionally navigate to login afterwards.
     * Uses: AuthService.logout
     */
    async logout(router?: Router) {
      this._busy(true);
      try {
        await AuthService.logout();
      } catch (e) {
        // even if logout call fails, we still clear local session
      } finally {
        this._wipe();
        if (router) {
          await router.push({ name: 'login' });
        }
      }
      this._busy(false);
    },

    /**
     * Signup new user. Leaves post-signup flow to the app (e.g., verify email).
     * Uses: AuthService.signup
     */
    async signup(email: string, password1: string, password2: string, name: string, router?: Router) {
      this._busy(true);
      try {
        await AuthService.signup(email, password1, password2, name);
        // Typically redirect to email verification page
        if (router) {
          await router.push({ name: 'verify-email' });
        }
        this._busy(false);
      } catch (e) {
        this._die(e);
      }
    },

    /**
     * Verify email with provided token/code.
     * Uses: AuthService.verifyEmail
     */
    async verifyEmail(token: string, router?: Router) {
      this._busy(true);
      try {
        const response = await AuthService.verifyEmail(token);
        // After verification, we often redirect to login
        if (router) {
          await router.push({ name: 'login' });
        }
        this._busy(false);
        return response;
      } catch (e) {
        this._die(e);
      }
    },

    /**
     * Fetch the current user from backend and align local session.
     * Uses: AuthService.fetchUser
     */
    async fetchUser() {
      this._busy(true);
      try {
        const user = await AuthService.fetchUser();
        // If backend returns null/undefined, treat as unauthenticated
        if (!user) {
          this._wipe();
        } else {
          this.user = user;
          this.isAuthenticated = true;
          this._persist();
        }
        this._busy(false);
      } catch (e) {
        // On failure (e.g., expired token), clear everything
        this._wipe();
        this._die(e, 'Failed to fetch user');
      }
    },

    /**
     * App bootstrap: if we think we're authenticated, refresh the user.
     * Uses: this.fetchUser (which calls AuthService.fetchUser)
     */
    async initialize() {
      if (!this.isAuthenticated) return;
      try {
        await this.fetchUser();
      } catch {
        // fetchUser already normalizes state and error
      }
    },
  },
});
