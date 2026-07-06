<template>
  <div class="ranking-list">
    <h3 class="section-title">
      <el-icon><Trophy /></el-icon> 图书总榜 TOP20
    </h3>
    <div class="rank-items">
      <div
        v-for="(book, idx) in books"
        :key="book.id"
        class="rank-item"
        @click="goDetail(book.id)"
      >
        <span class="rank-num" :class="medalClass(idx)">{{ idx + 1 }}</span>
        <img :src="book.cover" :alt="book.title" class="rank-cover" @error="onImgError" />
        <div class="rank-info">
          <p class="rank-title">{{ book.title }}</p>
          <p class="rank-score">
            <el-icon :size="14" color="#E67E22"><StarFilled /></el-icon>
            {{ book.rating?.toFixed(1) || 'N/A' }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

defineProps({
  books: { type: Array, default: () => [] },
})

const router = useRouter()
function goDetail(id) { router.push(`/book/${id}`) }

function medalClass(idx) {
  if (idx === 0) return 'gold'
  if (idx === 1) return 'silver'
  if (idx === 2) return 'bronze'
  return ''
}

function onImgError(e) {
  e.target.src = 'data:image/svg+xml,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="64"><rect width="48" height="64" fill="#f0ede8"/></svg>'
  )
}
</script>

<style scoped>
.ranking-list {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  position: sticky;
  top: 80px;
}
.section-title {
  font-size: 16px; color: #2C3E50;
  display: flex; align-items: center; gap: 6px;
  margin-bottom: 12px; padding-bottom: 10px;
  border-bottom: 2px solid #D4A24C;
}
.rank-items { display: flex; flex-direction: column; gap: 4px; }
.rank-item {
  display: flex; align-items: center; gap: 12px;
  cursor: pointer; padding: 10px; border-radius: 8px;
  transition: background 0.2s;
}
.rank-item:hover { background: #FFF8E7; }
.rank-num {
  width: 22px; text-align: center; font-size: 14px; font-weight: 700;
  color: #999; flex-shrink: 0;
}
.rank-num.gold { color: #D4A24C; font-size: 18px; }
.rank-num.silver { color: #95A5A6; font-size: 17px; }
.rank-num.bronze { color: #CD853F; font-size: 16px; }
.rank-cover { width: 42px; height: 56px; object-fit: cover; border-radius: 4px; flex-shrink: 0; }
.rank-info { flex: 1; min-width: 0; }
.rank-title { font-size: 13px; color: #2C3E50; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
.rank-score { font-size: 12px; color: #E67E22; display: flex; align-items: center; gap: 2px; margin-top: 2px; }
</style>
