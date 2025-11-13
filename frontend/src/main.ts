import './assets/index.css'
import './assets/styles/variables.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'

console.log(`WrAFT Version: ${__APP_VERSION__}`)

const app = createApp(App)
app.use(createPinia())
app.use(router)

const authStore = useAuthStore()
authStore.initialize().then(() => {
  app.mount('#app')
})
