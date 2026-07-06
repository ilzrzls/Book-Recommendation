<template>
  <div class="shelves-page">
    <div class="page-header">
      <h2>我的书架</h2>
      <p class="page-subtitle">管理你的阅读进度</p>
    </div>
    <ShelfManager />
  </div>
</template>

<script setup>
import ShelfManager from '../components/shelf/ShelfManager.vue'
</script>

<style scoped>
.shelves-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}
.page-header h2 {
  font-size: 24px;
  color: #2C3E50;
}
.page-subtitle {
  font-size: 14px;
  color: #999;
  margin-top: 4px;
}
</style>
