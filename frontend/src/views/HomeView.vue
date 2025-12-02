<template>
  <div class="home-view">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">Welcome to <span class="hero-title-highlight">WrAFT</span></h1>
        <p class="hero-subtitle">
          Writing Assessment and Feedback Tool is an AI-powered tool for assessing and providing
          feedback on your writing
        </p>

        <div class="feature-badges">
          <span class="feature-badge">TOEFL Scoring</span>
          <span class="feature-badge">Essay Analysis</span>
          <span class="feature-badge">Instant Feedback</span>
        </div>

        <router-link :to="{ name: 'login' }">
          <Button class="cta-button">
            Get Started
            <span class="cta-arrow">→</span>
          </Button>
        </router-link>
      </div>
    </section>

    <!-- Why Choose Section -->
    <section class="features-section">
      <div class="section-container">
        <h2 class="section-title">Why Choose WrAFT?</h2>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3 class="feature-card-title">ETS-Benchmarked Scoring</h3>
            <p class="feature-card-description">
              Get accurate 0–5 scores based on official TOEFL Independent Writing standards.
            </p>
            <div class="feature-card-highlight">Professional-grade evaluation</div>
          </div>

          <div class="feature-card">
            <div class="feature-icon">💬</div>
            <h3 class="feature-card-title">Comprehensive Feedback</h3>
            <p class="feature-card-description">
              Detailed analysis covering structure, arguments, grammar, and style improvements.
            </p>
            <div class="feature-card-highlight">Actionable insights for growth</div>
          </div>

          <div class="feature-card">
            <div class="feature-icon">🔒</div>
            <h3 class="feature-card-title">Anonymous & Secure</h3>
            <p class="feature-card-description">
              Your essays are processed securely with complete anonymization protection.
            </p>
            <div class="feature-card-highlight">Privacy-first approach</div>
          </div>
        </div>
      </div>
    </section>

    <!-- How It Works Section -->
    <section class="how-it-works-section">
      <div class="section-container">
        <h2 class="section-title">How It Works</h2>
        <div class="steps-grid">
          <div class="step-card">
            <div class="step-badge">01</div>
            <h3 class="step-card-title">Submit Your Essay</h3>
            <p class="step-card-description">
              Upload or paste your argumentative essay for analysis.
            </p>
          </div>

          <div class="step-card">
            <div class="step-badge">02</div>
            <h3 class="step-card-title">AI Analysis</h3>
            <p class="step-card-description">
              Our advanced AI evaluates structure, arguments, and language use.
            </p>
          </div>

          <div class="step-card">
            <div class="step-badge">03</div>
            <h3 class="step-card-title">Get Results</h3>
            <p class="step-card-description">
              Receive detailed feedback and actionable improvement suggestions.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Funding Acknowledgment Section -->
    <section class="funding-section">
      <div class="section-container">
        <p class="funding-text">
          The development of WrAFT was funded by the
          <a
            href="https://www.taf.or.jp/"
            target="_blank"
            rel="noopener noreferrer"
            class="funding-link"
          >
            Telecommunications Advancement Foundation in Japan
          </a>
        </p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button'
</script>

<style scoped>
/* Main Container */
.home-view {
  position: relative;
  min-height: 100vh;
  /* background: linear-gradient(180deg, #7b7ce6 0%, #a6b6f7 100%); */
  padding-bottom: 4rem;
}

/* Section Container */
.section-container {
  width: 100%;
  max-width: 72rem;
  margin: 0 auto;
  padding: 0 1rem;
}

/* Hero Section */
.hero-section {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 4rem 1rem 2rem;
  min-height: 60vh;
}

.hero-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  max-width: 48rem;
}

.hero-title {
  font-size: 2.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #fff;
  text-align: center;
  text-shadow: 0 2px 16px rgba(161, 140, 209, 0.25);
  line-height: 1.2;
}

.hero-title-highlight {
  background: linear-gradient(135deg, #ffeaa7, #fab1a0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.125rem;
  color: rgba(255, 255, 255, 0.9);
  text-align: center;
  line-height: 1.6;
  max-width: 42rem;
}

@media (min-width: 768px) {
  .hero-title {
    font-size: 3.5rem;
  }

  .hero-subtitle {
    font-size: 1.25rem;
  }
}

/* Feature Badges */
.feature-badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem;
  margin: 1rem 0;
}

.feature-badge {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 1.5rem;
  padding: 0.5rem 1.25rem;
  color: #fff;
  font-weight: 500;
  font-size: 0.875rem;
  box-shadow: 0 2px 8px rgba(161, 140, 209, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.18);
  transition: all 0.2s ease;
}

.feature-badge:hover {
  background: rgba(255, 255, 255, 0.25);
  box-shadow: 0 4px 16px rgba(161, 140, 209, 0.18);
  transform: translateY(-2px);
}

@media (min-width: 768px) {
  .feature-badge {
    font-size: 1rem;
    padding: 0.625rem 1.5rem;
  }
}

/* CTA Button */
.cta-button {
  background: linear-gradient(90deg, #21e6a3 0%, #3bb2f6 100%);
  color: #fff;
  border-radius: 1.5rem;
  font-weight: 600;
  font-size: 1rem;
  padding: 0.875rem 2rem;
  box-shadow: 0 2px 8px rgba(59, 178, 246, 0.15);
  border: none;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.cta-button:hover {
  background: linear-gradient(90deg, #1fd89b 0%, #249be6 100%);
  box-shadow: 0 4px 16px rgba(59, 178, 246, 0.25);
  transform: translateY(-2px);
}

.cta-arrow {
  font-size: 1.25rem;
  transition: transform 0.2s ease;
}

.cta-button:hover .cta-arrow {
  transform: translateX(4px);
}

@media (min-width: 768px) {
  .cta-button {
    font-size: 1.125rem;
    padding: 1rem 2.5rem;
  }
}

/* Section Title */
.section-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: #fff;
  margin-bottom: 2rem;
  text-align: center;
  text-shadow: 0 2px 10px rgba(161, 140, 209, 0.15);
}

@media (min-width: 768px) {
  .section-title {
    font-size: 2.25rem;
    margin-bottom: 3rem;
  }
}

/* Features Section */
.features-section {
  padding: 4rem 0;
}

.features-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
}

@media (min-width: 768px) {
  .features-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
  }
}

/* Feature Card */
.feature-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 1rem;
  padding: 2rem;
  text-align: left;
  transition: all 0.3s ease;
}

.feature-card:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  line-height: 1;
}

.feature-card-title {
  color: #fff;
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  line-height: 1.3;
}

.feature-card-description {
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.9375rem;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.feature-card-highlight {
  color: #7bffec;
  font-weight: 500;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

/* How It Works Section */
.how-it-works-section {
  padding: 4rem 0;
}

.steps-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}

@media (min-width: 768px) {
  .steps-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
  }
}

/* Step Card */
.step-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 1rem;
  padding: 2rem;
  text-align: center;
  position: relative;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.step-card:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.step-badge {
  position: absolute;
  top: -1rem;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #ff6b6b, #ee5a24);
  color: white;
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  box-shadow: 0 5px 15px rgba(238, 90, 36, 0.4);
  z-index: 1;
}

.step-card-title {
  color: #fff;
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  line-height: 1.3;
}

.step-card-description {
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.9375rem;
  line-height: 1.6;
}

/* Funding Section */
.funding-section {
  padding: 3rem 0 2rem;
  text-align: center;
}

.funding-text {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9375rem;
  line-height: 1.6;
}

.funding-link {
  color: #7bffec;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s ease;
  border-bottom: 1px solid transparent;
}

.funding-link:hover {
  color: #a8fff5;
  border-bottom-color: #a8fff5;
}

@media (min-width: 768px) {
  .funding-text {
    font-size: 1rem;
  }
}
</style>
