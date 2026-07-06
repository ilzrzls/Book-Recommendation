<template>
  <div class="skeleton-card">
    <div class="skeleton-cover"></div>
    <div class="skeleton-info">
      <div class="skeleton-line w-80"></div>
      <div class="skeleton-line w-50"></div>
      <div class="skeleton-line w-60"></div>
      <div class="skeleton-line w-90"></div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

.skeleton-cover {
  aspect-ratio: 3/4;
  background: linear-gradient(90deg, #e8e8e8 25%, #f5f5f5 50%, #e8e8e8 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-info {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-line {
  height: 14px;
  border-radius: 4px;
  background: linear-gradient(90deg, #e8e8e8 25%, #f5f5f5 50%, #e8e8e8 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
.w-80 { width: 80%; }
.w-50 { width: 50%; }
.w-60 { width: 60%; }
.w-90 { width: 90%; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
