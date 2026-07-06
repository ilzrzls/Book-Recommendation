<template>
  <div class="guess-you-like">
    <h3 class="section-title">
      <el-icon><Star /></el-icon> 猜你喜欢
    </h3>
    <div class="guess-list">
      <div
        v-for="book in books"
        :key="book.id"
        class="guess-item"
        @click="goDetail(book.id)"
      >
        <img :src="book.cover" :alt="book.title" class="guess-cover" />
        <div class="guess-info">
          <p class="guess-title">{{ book.title }}</p>
          <p class="guess-author">{{ book.author }}</p>
          <el-rate :model-value="book.rating / 2" disabled size="small" />
        </div>
      </div>
    </div>
    <el-empty v-if="books.length === 0" description="暂无推荐" :image-size="60" />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

defineProps({
  books: { type: Array, default: () => [] },
})

const router = useRouter()
function goDetail(id) { router.push(`/book/${id}`) }
</script>

<style scoped>
.guess-you-like {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  position: sticky;
  top: 80px;
}

.section-title {
  font-size: 16px;
  color: #2C3E50;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.guess-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.guess-item {
  display: flex;
  gap: 10px;
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  transition: background 0.2s;
}
.guess-item:hover {
  background: #F8F9FA;
}

.guess-cover {
  width: 48px;
  height: 64px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}

.guess-info {
  flex: 1;
  min-width: 0;
}

.guess-title {
  font-size: 14px;
  font-weight: 600;
  color: #2C3E50;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.guess-author {
  font-size: 12px;
  color: #999;
  margin: 2px 0 4px;
}
</style>
