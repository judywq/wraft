<template>
  <div class="flex flex-col relative">

    <!-- Main Content -->
    <div class="flex-1 flex flex-col items-center justify-center text-center px-4">
      <div class="flex flex-col items-center space-y-4 mt-8">
        <h1 class="main-title">Welcome to <span class="highlight">WrAFT</span></h1>
        <p class="main-subtitle">Advanced Writing Evaluator – Your AI-powered companion for <br />ETS-benchmarked scoring and comprehensive feedback</p>
        <div class="flex flex-wrap justify-center gap-2 mb-4">
          <span class="feature-badge">TOEFL Scoring</span>
          <span class="feature-badge">Essay Analysis</span>
          <span class="feature-badge">Instant Feedback</span>
        </div>
        <router-link :to="{ name: 'login' }">
          <Button class="modern-btn">Get Started →</Button>
        </router-link>
      </div>

      <!-- Why Choose Section -->
      <section class="mt-16 w-full max-w-4xl mx-auto">
        <h2 class="section-title">Why Choose WrAFT?</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="bg-white/10 rounded-xl p-6 text-white shadow">
            <div class="mb-2 text-2xl">📊</div>
            <h3 class="card-title">ETS-Benchmarked Scoring</h3>
            <p class="card-desc">Get accurate 0–5 scores based on official TOEFL Independent Writing standards.</p>
            <div class="card-highlight">Professional-grade evaluation</div>
          </div>
          <div class="bg-white/10 rounded-xl p-6 text-white shadow">
            <div class="mb-2 text-2xl">💬</div>
            <h3 class="card-title">Comprehensive Feedback</h3>
            <p class="card-desc">Detailed analysis covering structure, arguments, grammar, and style improvements.</p>
            <div class="card-highlight">Actionable insights for growth</div>
          </div>
          <div class="bg-white/10 rounded-xl p-6 text-white shadow">
            <div class="mb-2 text-2xl">🔒</div>
            <h3 class="card-title">Anonymous & Secure</h3>
            <p class="card-desc">Your essays are processed securely with complete anonymization protection.</p>
            <div class="card-highlight">Privacy-first approach</div>
          </div>
        </div>
      </section>

      <!-- How It Works Section -->
      <section class="mt-16 w-full max-w-4xl mx-auto">
        <h2 class="section-title">How It Works</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="bg-white/10 rounded-xl p-6 text-white shadow flex flex-col items-center relative">
            <div class="step-badge">01</div>
            <h3 class="card-title mt-4">Submit Your Essay</h3>
            <p class="card-desc">Upload or paste your argumentative essay for analysis.</p>
          </div>
          <div class="bg-white/10 rounded-xl p-6 text-white shadow flex flex-col items-center relative">
            <div class="step-badge">02</div>
            <h3 class="card-title mt-4">AI Analysis</h3>
            <p class="card-desc">Our advanced AI evaluates structure, arguments, and language use.</p>
          </div>
          <div class="bg-white/10 rounded-xl p-6 text-white shadow flex flex-col items-center relative">
            <div class="step-badge">03</div>
            <h3 class="card-title mt-4">Get Results</h3>
            <p class="card-desc">Receive detailed feedback and actionable improvement suggestions.</p>
          </div>
        </div>
      </section>


    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Button from '@/components/ui/button/Button.vue'
import deepLevelScreenshot from '@/assets/imgs/deep-level screenshot.png'

const showModal = ref(false)
</script>

<style scoped>
body {
  background: linear-gradient(180deg, #7b7ce6 0%, #a6b6f7 100%);
}

.main-title {
  font-size: 2.8rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 0.5rem;
  color: #fff;
  text-align: center;
  text-shadow: 0 2px 16px rgba(161,140,209,0.25);
}

.main-subtitle {
  font-size: 1.25rem;
  color: #e0e0e0;
  text-align: center;
  margin-bottom: 2rem;
}

.section-title {
  font-size: 2rem;
  font-weight: 600;
  color: #fff;
  margin-bottom: 1.5rem;
  text-align: center;
  text-shadow: 0 2px 10px rgba(161,140,209,0.15);
}

.card-title {
  color: #fff;
  font-size: 1.15rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.card-desc {
  color: #e0e0e0;
  font-size: 1rem;
  margin-bottom: 1rem;
}

.card-highlight {
  color: #7bffec;
  font-weight: 500;
  font-size: 0.95rem;
}

.feature-badge {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 1.5rem;
  padding: 0.5rem 1.5rem;
  color: #fff;
  font-weight: 500;
  font-size: 1rem;
  margin: 0 0.25rem;
  box-shadow: 0 2px 8px rgba(161,140,209,0.10);
  border: 1px solid rgba(255,255,255,0.18);
  transition: background 0.2s, box-shadow 0.2s;
}
.feature-badge:hover {
  background: rgba(255,255,255,0.25);
  box-shadow: 0 4px 16px rgba(161,140,209,0.18);
}

.modern-btn {
  background: linear-gradient(90deg, #21e6a3 0%, #3bb2f6 100%);
  color: #fff;
  border-radius: 1.5rem;
  font-weight: 600;
  font-size: 1.1rem;
  padding: 0.75rem 2rem;
  box-shadow: 0 2px 8px rgba(59,178,246,0.15);
  border: none;
  transition: background 0.2s, box-shadow 0.2s;
}
.modern-btn:hover {
  background: linear-gradient(90deg, #1fd89b 0%, #249be6 100%);
  box-shadow: 0 4px 16px rgba(59,178,246,0.25);
}
.modern-btn.secondary {
  background: #e3eafe;
  color: #3bb2f6;
  border: 1.5px solid #3bb2f6;
}
.modern-btn.secondary:hover {
  background: #d0e3fa;
  color: #249be6;
}

.cta-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #fff;
  margin-bottom: 1.5rem;
  text-align: center;
}

.stat-number {
  font-size: 2rem;
  font-weight: bold;
  color: #7bffec;
  line-height: 1;
}

.stat-label {
  font-size: 0.95rem;
  color: #e0e0e0;
  margin-top: 0.25rem;
}

.step-badge {
  position: absolute;
  top: -15px;
  left: 30px;
  background: linear-gradient(135deg, #ff6b6b, #ee5a24);
  color: white;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1rem;
  box-shadow: 0 5px 15px rgba(238, 90, 36, 0.4);
}
</style>
