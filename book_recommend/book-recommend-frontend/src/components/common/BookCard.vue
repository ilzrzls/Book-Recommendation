<template>
  <div class="book-card" :class="{ dismissed }" @click="goDetail">
    <div class="card-cover">
      <img :src="book.cover" :alt="book.title" @error="onImgError" />
      <div v-if="book.is_free === true" class="free-badge">免费</div>
      <div v-else-if="book.is_free === false" class="paid-badge">付费</div>
      <!-- Reading progress badge -->
      <div v-if="progress > 0 && progress < 100" class="progress-badge">
        {{ progress }}%
      </div>
      <div v-if="progress === 100" class="read-badge">
        已读
      </div>
    </div>
    <div class="card-info">
      <h3 class="card-title" :title="book.title">{{ book.title }}</h3>
      <p class="card-author">{{ book.author }}</p>
      <div class="card-rating" v-if="book.rating">
        <el-rate :model-value="book.rating / 2" disabled text-color="#D4A24C" class="card-rate" />
        <span class="card-score">{{ book.rating?.toFixed(1) }}</span>
      </div>
      <!-- Action buttons -->
      <div v-if="showActions" class="card-actions" @click.stop>
        <el-button size="small" type="primary" plain @click="handleLike">感兴趣</el-button>
        <el-button size="small" plain @click="handleDislike">不感兴趣</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../../api/request'

const props = defineProps({
  book: { type: Object, required: true },
  progress: { type: Number, default: 0 },
  showActions: { type: Boolean, default: false },
})

const emit = defineEmits(['dismiss'])
const router = useRouter()
const dismissed = ref(false)

function goDetail() {
  router.push(`/book/${props.book.id}`)
}

async function handleLike() {
  try {
    await request.post('/user/feedback', { book_id: props.book.id, interested: true })
  } catch { /* ignore */ }
  ElMessage.success({ message: '已记录偏好，将推荐更多类似好书', duration: 1500 })
  setTimeout(() => { dismissed.value = true; emit('dismiss', props.book.id) }, 400)
}

async function handleDislike() {
  try {
    await request.post('/user/feedback', { book_id: props.book.id, interested: false })
  } catch { /* ignore */ }
  ElMessage.info({ message: '已记录，将减少此类推荐', duration: 1500 })
  setTimeout(() => { dismissed.value = true; emit('dismiss', props.book.id) }, 400)
}

function onImgError(e) {
  // Generate colored placeholder on error
  const el = e.target
  const title = props.book.title || '?'
  const colors = ['#2C3E50','#8E44AD','#2980B9','#27AE60','#D35400','#C0392B']
  const c = colors[Math.abs(title.length) % colors.length]
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="240" height="320"><rect width="240" height="320" fill="${c}"/><text x="120" y="150" text-anchor="middle" fill="white" font-size="24">${title.slice(0,4)}</text><text x="120" y="180" text-anchor="middle" fill="rgba(255,255,255,0.5)" font-size="12">No Cover</text></svg>`
  el.src = 'data:image/svg+xml,' + encodeURIComponent(svg)
}

function formatCount(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n.toString()
}
</script>

<style scoped>
.book-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.4s ease;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
}
.book-card.dismissed {
  opacity: 0;
  transform: scale(0.9);
  pointer-events: none;
  margin-bottom: -20px;
}
.book-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}

.card-cover {
  position: relative;
  aspect-ratio: 3/4;
  overflow: hidden;
  background: #f0f0f0;
}
.free-badge { position:absolute; top:6px; left:6px; background:#27AE60; color:#fff; padding:2px 6px; border-radius:8px; font-size:10px; font-weight:bold; z-index:2; }
.paid-badge { position:absolute; top:6px; left:6px; background:rgba(0,0,0,0.55); color:#fff; padding:2px 6px; border-radius:8px; font-size:10px; z-index:2; }
.card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.progress-badge {
  position: absolute;
  bottom: 6px;
  right: 6px;
  background: #E67E22;
  color: #fff;
  padding: 1px 6px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: bold;
}

.read-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  background: #2E4A3A;
  color: #fff;
  padding: 1px 6px;
  border-radius: 8px;
  font-size: 10px;
}

.card-info {
  padding: 10px 8px 14px 8px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #2C3E50;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 0;
  line-height: 1.25;
}

.card-author {
  font-size: 10px;
  color: #888;
  margin-bottom: 0;
  line-height: 1.2;
}

.card-rating {
  display: flex;
  align-items: center;
  margin-bottom: 0;
}
.card-rate { --el-rate-icon-size: 14px; }
.card-score { font-size: 11px; color: #D4A24C; margin-left: 2px; flex-shrink: 0; }

.card-actions {
  display: flex;
  gap: 4px;
  margin-top: auto;
  padding-top: 2px;
  justify-content: center;
}
.card-actions :deep(.el-button--small) { font-size: 11px; padding: 3px 11px; height: auto; }
</style>
