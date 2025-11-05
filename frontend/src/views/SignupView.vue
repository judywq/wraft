<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Loader2 } from 'lucide-vue-next'
import { storeToRefs } from 'pinia'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import * as z from 'zod'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { signupFormSchema } from '@/lib/validations'
import { Checkbox } from '@/components/ui/checkbox'

const authStore = useAuthStore()
const { loading } = storeToRefs(authStore)
const router = useRouter()
const generalError = ref<string | null>(null)

const form = useForm({
  validationSchema: toTypedSchema(signupFormSchema),
  initialValues: {
    email: '',
    password1: '',
    password2: '',
    name: '',
  },
})

const onSubmit = form.handleSubmit(async (values) => {
  try {
    generalError.value = null
    await authStore.signup(values.email, values.password1, values.password2, values.name, router)
  } catch (err: any) {
    if (err.fieldErrors) {
      form.setErrors(err.fieldErrors)
    }
    if (err.nonFieldError) {
      generalError.value = err.nonFieldError
    }
  }
})

const signupWithGoogle = () => {
  // TODO: Implement Google OAuth signup
  console.log('Google signup clicked');
};

const signupWithGithub = () => {
  // TODO: Implement GitHub OAuth signup
  console.log('GitHub signup clicked');
};
</script>

<template>
  <div class="signup-container">
    <!-- Floating background elements -->
    <div class="floating-orbs">
      <div class="orb" v-for="n in 5" :key="n" :class="`orb-${n}`"></div>
    </div>

    <div class="main-container">
      <!-- Signup Card -->
      <div class="signup-section">
        <div class="signup-card">
          <!-- Avatar Section -->
          <div class="signup-avatar">
            <div class="avatar-ring"></div>
            <div class="avatar-core">🎓</div>
          </div>

          <!-- Title and Subtitle -->
          <div class="signup-header-text">
            <h1 class="signup-title">Create an Account</h1>
            <p class="signup-subtitle">Join WrAFT to start your learning journey</p>
          </div>

          <!-- Signup Form -->
          <form @submit="onSubmit" class="signup-form">
            <FormField
              v-slot="{ componentField }"
              name="email"
            >
              <FormItem>
                <FormLabel class="form-label">
                  <span class="label-icon">📧</span>
                  Email
                </FormLabel>
                <FormControl>
                  <Input
                    v-bind="componentField"
                    type="email"
                    placeholder="name@example.com"
                    :disabled="loading"
                    class="form-input"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>

            <FormField
              v-slot="{ componentField }"
              name="name"
            >
              <FormItem>
                <FormLabel class="form-label">
                  <span class="label-icon">👤</span>
                  Full Name
                </FormLabel>
                <FormControl>
                  <Input
                    v-bind="componentField"
                    type="text"
                    placeholder="Enter your full name"
                    :disabled="loading"
                    class="form-input"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>

            <FormField
              v-slot="{ componentField }"
              name="password1"
            >
              <FormItem>
                <FormLabel class="form-label">
                  <span class="label-icon">🔒</span>
                  Password
                </FormLabel>
                <FormControl>
                  <Input
                    v-bind="componentField"
                    type="password"
                    placeholder="Create a password"
                    :disabled="loading"
                    class="form-input"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>

            <FormField
              v-slot="{ componentField }"
              name="password2"
            >
              <FormItem>
                <FormLabel class="form-label">
                  <span class="label-icon">🔐</span>
                  Confirm Password
                </FormLabel>
                <FormControl>
                  <Input
                    v-bind="componentField"
                    type="password"
                    placeholder="Confirm your password"
                    :disabled="loading"
                    class="form-input"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            </FormField>

            <div v-if="generalError" class="text-destructive text-sm">
              {{ generalError }}
            </div>

            <Button
              type="submit"
              class="signup-button"
              :disabled="loading || !form.meta.value.valid"
            >
              <Loader2
                v-if="loading"
                class="mr-2 h-4 w-4 animate-spin"
              />
              {{ loading ? 'Creating account...' : 'Create Account' }}
            </Button>

            <div class="login-prompt">
              Already have an account?
              <router-link
                :to="{ name: 'login' }"
                class="login-link"
                :tabindex="loading ? -1 : 0"
              >
                Sign in
              </router-link>
            </div>
          </form>
        </div>

        <!-- Side Features -->
        <div class="signup-features">
          <div class="feature-item">
            <div class="feature-icon">📊</div>
            <div class="feature-content">
              <h3>ETS-Benchmarked Scoring</h3>
              <p>Get accurate TOEFL-standard evaluations</p>
            </div>
          </div>

          <div class="feature-item">
            <div class="feature-icon">💬</div>
            <div class="feature-content">
              <h3>Detailed Feedback</h3>
              <p>Comprehensive analysis and suggestions</p>
            </div>
          </div>

          <div class="feature-item">
            <div class="feature-icon">🔒</div>
            <div class="feature-content">
              <h3>Secure & Private</h3>
              <p>Your essays are anonymized and protected</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.signup-container {
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  /* min-height: 100vh; */
  position: relative;
}

/* Floating background elements */
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

.orb-1 { width: 100px; height: 100px; top: 15%; left: 8%; animation-delay: 0s; }
.orb-2 { width: 60px; height: 60px; top: 70%; right: 20%; animation-delay: -8s; }
.orb-3 { width: 80px; height: 80px; bottom: 20%; left: 15%; animation-delay: -15s; }
.orb-4 { width: 120px; height: 120px; top: 40%; right: 10%; animation-delay: -5s; }
.orb-5 { width: 40px; height: 40px; top: 60%; left: 50%; animation-delay: -12s; }

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); opacity: 0.3; }
  25% { transform: translateY(-40px) rotate(90deg); opacity: 0.6; }
  50% { transform: translateY(-20px) rotate(180deg); opacity: 0.4; }
  75% { transform: translateY(-60px) rotate(270deg); opacity: 0.7; }
}

.main-container {
  position: relative;
  z-index: 2;
  /* min-height: 100vh; */
  display: flex;
  flex-direction: column;
  padding: 2rem;
}

/* Header */
.signup-header {
  display: flex;
  justify-content: center;
  margin-bottom: 2rem;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: white;
  font-weight: 600;
  font-size: 1.5rem;
}

.brand-icon {
  font-size: 2rem;
}

/* Signup Section */
.signup-section {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 4rem;
  max-width: 1000px;
  margin: 0 auto;
  align-items: center;
}

.signup-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 25px;
  padding: 3rem;
  width: 100%;
  max-width: 450px;
  transition: all 0.3s ease;
}

.signup-card:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-5px);
}

/* Avatar */
.signup-avatar {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0 auto 2rem;
}

.avatar-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.1));
  backdrop-filter: blur(20px);
  animation: spin 20s linear infinite;
}

.avatar-core {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ffeaa7, #fab1a0);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  box-shadow: 0 15px 35px rgba(0,0,0,0.2);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Header Text */
.signup-header-text {
  text-align: center;
  margin-bottom: 2.5rem;
}

.signup-title {
  font-size: 2.5rem;
  font-weight: 300;
  color: white;
  margin-bottom: 0.5rem;
  text-shadow: 0 2px 15px rgba(0,0,0,0.3);
}

.signup-subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: 1rem;
  line-height: 1.5;
}

/* Form */
.signup-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.form-label {
  color: white;
  font-weight: 500;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.label-icon {
  font-size: 1rem;
}

.form-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  padding: 1rem;
  color: white;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s ease;
}

.form-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.form-input:focus {
  border-color: #74b9ff;
  background: rgba(255, 255, 255, 0.15);
}

/* Checkbox */
.checkbox-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.checkbox-content {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

/* Signup Button */
.signup-button {
  background: linear-gradient(135deg, #00b894, #55a3ff);
  border: none;
  color: white;
  padding: 1rem 2rem;
  border-radius: 15px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 10px 25px rgba(0, 184, 148, 0.4);
  margin-top: 0.5rem;
}

.signup-button:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 15px 35px rgba(0, 184, 148, 0.6);
}

.signup-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Divider */
.signup-divider {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1.5rem 0;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: rgba(255, 255, 255, 0.3);
}

.divider-text {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
}

/* Social Signup */
.social-signup {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 2rem;
}

.social-button {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 0.75rem;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-weight: 500;
}

.social-button:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.social-icon {
  font-size: 1.1rem;
}

/* Login Prompt */
.login-prompt {
  text-align: center;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}

.login-link {
  color: #74b9ff;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.login-link:hover {
  color: #0984e3;
}

/* Features */
.signup-features {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  padding-left: 2rem;
}

.feature-item {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.feature-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.feature-content h3 {
  color: white;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.3rem;
}

.feature-content p {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
  line-height: 1.4;
}

/* Responsive */
@media (max-width: 968px) {
  .signup-section {
    grid-template-columns: 1fr;
    gap: 2rem;
  }

  .signup-features {
    padding-left: 0;
    grid-row: 1;
  }

  .signup-card {
    grid-row: 2;
  }
}

@media (max-width: 768px) {
  .main-container {
    padding: 1rem;
  }

  .signup-card {
    padding: 2rem;
  }

  .signup-title {
    font-size: 2rem;
  }

  .signup-features {
    display: none;
  }

  .social-signup {
    grid-template-columns: 1fr;
  }
}

/* Animations */
.signup-card {
  animation: fadeInUp 0.6s ease-out;
}

.signup-features {
  animation: fadeInRight 0.8s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
