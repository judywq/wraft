// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// ----- Route factories -----
const DefaultLayout = () => import('@/layouts/DefaultLayout.vue')
const AuthLayout = () => import('@/layouts/AuthLayout.vue')

// App views (lazy-loaded for consistency)
const HomeView = () => import('@/views/HomeView.vue')
const EvaluationView = () => import('@/views/EvaluationView.vue')
const ResultView = () => import('@/views/ResultView.vue')
const ResultListView = () => import('@/views/ResultListView.vue')
const UpdatePasswordView = () => import('@/views/auth/UpdatePasswordView.vue')

// Auth views
const LoginView = () => import('@/views/auth/LoginView.vue')
const RegisterView = () => import('@/views/auth/RegisterView.vue')
const EmailVerificationView = () => import('@/views/auth/EmailVerificationView.vue')
const RequestPasswordResetView = () => import('@/views/auth/RequestPasswordResetView.vue')
const SetNewPasswordView = () => import('@/views/auth/SetNewPasswordView.vue')
const ResetLinkSentView = () => import('@/views/auth/ResetLinkSentView.vue')

// Misc
const NotFoundView = () => import('@/views/NotFoundView.vue')

// ----- Route definitions -----
const appChildren = [
  {
    path: '',
    name: 'home',
    component: HomeView,
  },
  {
    path: 'evaluate',
    name: 'evaluate',
    component: EvaluationView,
    meta: { requiresAuth: true },
  },
  {
    path: 'result/:id',
    name: 'result',
    component: ResultView,
    meta: { requiresAuth: true },
  },
  {
    path: 'change-password',
    name: 'change-password',
    component: UpdatePasswordView,
    meta: { requiresAuth: true },
  },
  {
    // note: relative child path still resolves to "/history"
    path: 'history',
    name: 'history',
    component: ResultListView,
    meta: { requiresAuth: true },
  },
]

const authChildren = [
  { path: 'login', name: 'login', component: LoginView },
  { path: 'signup', name: 'signup', component: RegisterView },
  { path: 'verify-email', name: 'verify-email', component: EmailVerificationView },
  // Password Reset Flow
  { path: 'forgot-password', name: 'forgot-password', component: RequestPasswordResetView },
  { path: 'reset-password/:uid/:token', name: 'reset-password', component: SetNewPasswordView },
  { path: 'password-reset-sent', name: 'password-reset-sent', component: ResetLinkSentView },
]

const routes = [
  {
    path: '/',
    component: DefaultLayout,
    children: appChildren,
  },
  {
    path: '/auth',
    name: 'auth',
    component: AuthLayout,
    meta: { requiresGuest: true },
    children: authChildren,
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: NotFoundView,
  },
]

// ----- Router instance -----
const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ----- Navigation guards -----
const needsAuth = (to) => to.matched.some((r) => r.meta?.requiresAuth)
const needsGuest = (to) => to.matched.some((r) => r.meta?.requiresGuest)

router.beforeEach((to) => {
  const { isAuthenticated } = useAuthStore()

  // Guard: protected pages
  if (needsAuth(to) && !isAuthenticated) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  // Guard: guest-only pages (e.g., /auth/*)
  if (needsGuest(to) && isAuthenticated) {
    return { name: 'evaluate' }
  }

  // otherwise, proceed
  return true
})

export default router
