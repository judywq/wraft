<template>
  <div class="not-found-view">
    <div class="not-found-content">
      <div class="not-found-illustration">
        <div class="not-found-number">404</div>
        <div class="not-found-icon">🔍</div>
      </div>
      
      <h1 class="not-found-title">Page Not Found</h1>
      <p class="not-found-description">
        The page you're looking for doesn't exist or has been moved.
      </p>
      
      <div class="not-found-actions">
        <router-link :to="{ name: 'home' }">
          <Button class="not-found-button" size="lg">
            <span>🏠</span>
            Return Home
          </Button>
        </router-link>
        <Button 
          variant="outline" 
          size="lg"
          @click="$router.go(-1)"
          class="not-found-button"
        >
          <span>←</span>
          Go Back
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button'
</script>

<style scoped>
/* Main Container */
.not-found-view {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  background: hsl(var(--background));
}

/* Content Container */
.not-found-content {
  max-width: 28rem;
  width: 100%;
  text-align: center;
}

/* Illustration */
.not-found-illustration {
  position: relative;
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 12rem;
}

.not-found-number {
  font-size: 8rem;
  font-weight: 800;
  line-height: 1;
  color: hsl(var(--muted));
  opacity: 0.3;
  position: absolute;
  z-index: 0;
}

.not-found-icon {
  font-size: 4rem;
  position: relative;
  z-index: 1;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-1rem);
  }
}

/* Title */
.not-found-title {
  font-size: 2rem;
  font-weight: 700;
  color: hsl(var(--foreground));
  margin-bottom: 1rem;
  line-height: 1.2;
}

@media (min-width: 768px) {
  .not-found-title {
    font-size: 2.5rem;
  }
}

/* Description */
.not-found-description {
  font-size: 1rem;
  color: hsl(var(--muted-foreground));
  margin-bottom: 2rem;
  line-height: 1.6;
}

@media (min-width: 768px) {
  .not-found-description {
    font-size: 1.125rem;
  }
}

/* Actions */
.not-found-actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: stretch;
}

@media (min-width: 640px) {
  .not-found-actions {
    flex-direction: row;
    justify-content: center;
  }
}

.not-found-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-weight: 600;
  transition: all 0.2s ease;
}

.not-found-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>
