<template>
  <div class="feed-list">
    <div class="feed-grid">
      <BookCard
        v-for="book in books"
        :key="book.id"
        :book="book"
        :show-actions="true"
      />
    </div>
    <!-- Loading skeleton -->
    <div v-if="loading" class="feed-grid">
      <SkeletonCard v-for="i in 8" :key="'skel-'+i" />
    </div>
    <!-- Empty state -->
    <el-empty v-if="!loading && books.length === 0" description="暂无推荐图书" />
  </div>
</template>

<script setup>
import BookCard from '../common/BookCard.vue'
import SkeletonCard from '../common/SkeletonCard.vue'

defineProps({
  books: { type: Array, required: true },
  loading: { type: Boolean, default: false },
})
</script>

<style scoped>
.feed-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
}

@media (max-width: 768px) {
  .feed-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
  }
}
</style>
