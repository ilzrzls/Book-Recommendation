<template>
  <div class="home-page">
    <div class="home-layout">
      <!-- ========== 左侧：4 个横向滚动栏目 ========== -->
      <div class="main-content" ref="mainContent">

        <!-- 栏目1：为你推荐 / 热门推荐 -->
        <div class="section-row">
          <div class="section-header">
            <h3 class="section-title gold-title">
              <el-icon><StarFilled /></el-icon>
              {{ userStore.isLoggedIn ? '为你推荐' : '热门推荐' }}
            </h3>
            <div class="arrow-btns">
              <button class="arrow-btn" @click="scrollRow('feed', -1)" :disabled="!canScrollLeft('feed')">
                <el-icon><ArrowLeft /></el-icon>
              </button>
              <button class="arrow-btn" @click="scrollRow('feed', 1)" :disabled="!canScrollRight('feed')">
                <el-icon><ArrowRight /></el-icon>
              </button>
            </div>
          </div>
          <div class="scroll-row" ref="feedRow" @scroll="updateArrows('feed')">
            <div v-if="loading" class="scroll-loading">
              <SkeletonCard v-for="i in 6" :key="'skel-'+i" class="scroll-card" />
            </div>
            <div v-else-if="feedBooks.length === 0" class="scroll-empty">
              <el-empty description="暂无推荐图书" :image-size="80" />
            </div>
            <BookCard
              v-for="book in feedBooks" :key="book.id" :book="book"
              :show-actions="userStore.isLoggedIn" class="scroll-card"
              @dismiss="handleDismiss"
            />
          </div>
        </div>

        <!-- 栏目2：免费榜 -->
        <div class="section-row">
          <div class="section-header">
            <h3 class="section-title"><el-icon><Present /></el-icon> 免费榜</h3>
            <div class="arrow-btns">
              <button class="arrow-btn" @click="scrollRow('free', -1)" :disabled="!canScrollLeft('free')">
                <el-icon><ArrowLeft /></el-icon>
              </button>
              <button class="arrow-btn" @click="scrollRow('free', 1)" :disabled="!canScrollRight('free')">
                <el-icon><ArrowRight /></el-icon>
              </button>
            </div>
          </div>
          <div class="scroll-row" ref="freeRow" @scroll="updateArrows('free')">
            <div v-if="freeBooks.length === 0" class="scroll-loading">
              <SkeletonCard v-for="i in 6" :key="'skel-free-'+i" class="scroll-card" />
            </div>
            <BookCard v-for="book in freeBooks" :key="'free-'+book.id" :book="book" :show-actions="false" class="scroll-card" />
          </div>
        </div>

        <!-- 栏目3：付费榜 -->
        <div class="section-row">
          <div class="section-header">
            <h3 class="section-title"><el-icon><Goods /></el-icon> 付费榜</h3>
            <div class="arrow-btns">
              <button class="arrow-btn" @click="scrollRow('paid', -1)" :disabled="!canScrollLeft('paid')">
                <el-icon><ArrowLeft /></el-icon>
              </button>
              <button class="arrow-btn" @click="scrollRow('paid', 1)" :disabled="!canScrollRight('paid')">
                <el-icon><ArrowRight /></el-icon>
              </button>
            </div>
          </div>
          <div class="scroll-row" ref="paidRow" @scroll="updateArrows('paid')">
            <div v-if="paidBooks.length === 0" class="scroll-loading">
              <SkeletonCard v-for="i in 6" :key="'skel-paid-'+i" class="scroll-card" />
            </div>
            <BookCard v-for="book in paidBooks" :key="'paid-'+book.id" :book="book" :show-actions="false" class="scroll-card" />
          </div>
        </div>

        <!-- 栏目4：现代文学榜 -->
        <div class="section-row">
          <div class="section-header">
            <h3 class="section-title"><el-icon><Reading /></el-icon> 现代文学榜</h3>
            <div class="arrow-btns">
              <button class="arrow-btn" @click="scrollRow('literature', -1)" :disabled="!canScrollLeft('literature')">
                <el-icon><ArrowLeft /></el-icon>
              </button>
              <button class="arrow-btn" @click="scrollRow('literature', 1)" :disabled="!canScrollRight('literature')">
                <el-icon><ArrowRight /></el-icon>
              </button>
            </div>
          </div>
          <div class="scroll-row" ref="literatureRow" @scroll="updateArrows('literature')">
            <div v-if="literatureBooks.length === 0" class="scroll-loading">
              <SkeletonCard v-for="i in 6" :key="'skel-lit-'+i" class="scroll-card" />
            </div>
            <BookCard v-for="book in literatureBooks" :key="'lit-'+book.id" :book="book" :show-actions="false" class="scroll-card" />
          </div>
        </div>
      </div>

      <!-- ========== 右侧：TOP20 ========== -->
      <aside class="sidebar">
        <RankingList :books="topBooks" />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useUserStore } from '../stores/user'
import { booksAPI } from '../api/books'
import BookCard from '../components/common/BookCard.vue'
import SkeletonCard from '../components/common/SkeletonCard.vue'
import RankingList from '../components/home/RankingList.vue'

const userStore = useUserStore()

const feedBooks = ref([])
const freeBooks = ref([])
const paidBooks = ref([])
const literatureBooks = ref([])
const topBooks = ref([])
const loading = ref(false)

const feedRow = ref(null)
const freeRow = ref(null)
const paidRow = ref(null)
const literatureRow = ref(null)

const scrollState = reactive({
  feed: { canLeft: false, canRight: true },
  free: { canLeft: false, canRight: true },
  paid: { canLeft: false, canRight: true },
  literature: { canLeft: false, canRight: true },
})

function getRowRef(key) {
  const map = { feed: feedRow, free: freeRow, paid: paidRow, literature: literatureRow }
  return map[key]?.value
}
function canScrollLeft(key) { return scrollState[key]?.canLeft ?? false }
function canScrollRight(key) { return scrollState[key]?.canRight ?? false }

function updateArrows(key) {
  const el = getRowRef(key)
  if (!el) return
  const threshold = 4
  scrollState[key].canLeft = el.scrollLeft > threshold
  scrollState[key].canRight = el.scrollLeft + el.clientWidth < el.scrollWidth - threshold
}

function scrollRow(key, direction) {
  const el = getRowRef(key)
  if (!el) return
  const cardWidth = 184
  el.scrollBy({ left: cardWidth * 4 * direction, behavior: 'smooth' })
}

function handleDismiss(bookId) {
  feedBooks.value = feedBooks.value.filter(b => b.id !== bookId)
}

async function loadFeed() {
  loading.value = true
  try {
    const res = await booksAPI.getFeed()
    if (res.code === 200) feedBooks.value = res.data.items
  } finally {
    loading.value = false
    await nextTick(); updateArrows('feed')
  }
}
async function loadFreeRank() {
  try {
    const res = await booksAPI.getFreeRank()
    if (res.code === 200) freeBooks.value = res.data.items
  } catch { /* ignore */ }
  await nextTick(); updateArrows('free')
}
async function loadPaidRank() {
  try {
    const res = await booksAPI.getPaidRank()
    if (res.code === 200) paidBooks.value = res.data.items
  } catch { /* ignore */ }
  await nextTick(); updateArrows('paid')
}
async function loadModernLiterature() {
  try {
    const res = await booksAPI.getModernLiterature()
    if (res.code === 200) literatureBooks.value = res.data.items
  } catch { /* ignore */ }
  await nextTick(); updateArrows('literature')
}
async function loadTop() {
  try {
    const res = await booksAPI.getTop()
    if (res.code === 200) topBooks.value = res.data.items
  } catch { /* ignore */ }
}

onMounted(async () => {
  await Promise.all([loadFeed(), loadFreeRank(), loadPaidRank(), loadModernLiterature(), loadTop()])
})
</script>

<style scoped>
.home-page { max-width: 100%; margin: 0 auto; padding: 0 20px; height: calc(100vh - 120px); display: flex; flex-direction: column; overflow: hidden; }
.home-layout { display: flex; gap: 16px; flex: 1; min-height: 0; overflow: hidden; }
.main-content { flex: 1; min-width: 0; overflow-y: auto; overflow-x: hidden; padding-right: 4px; scrollbar-width: none; -ms-overflow-style: none; }
.main-content::-webkit-scrollbar { width: 0 !important; height: 0 !important; display: none !important; background: transparent; }
.sidebar { width: 280px; flex-shrink: 0; overflow-y: auto; overflow-x: hidden; scrollbar-width: none; -ms-overflow-style: none; }
.sidebar::-webkit-scrollbar { width: 0 !important; height: 0 !important; display: none !important; background: transparent; }
.section-row { margin-bottom: 24px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.section-title { font-size: 17px; font-weight: 600; color: #2C3E50; display: flex; align-items: center; gap: 6px; margin: 0; padding-bottom: 8px; border-bottom: 2px solid #D4A24C; }
.gold-title { color: #D4A24C; border-bottom-color: #D4A24C; }
.arrow-btns { display: flex; gap: 6px; flex-shrink: 0; }
.arrow-btn { width: 36px; height: 36px; border-radius: 50%; border: none; background: rgba(128,128,128,0.12); cursor: pointer; display: flex; align-items: center; justify-content: center; color: #1a2a4a; transition: all 0.25s; }
.arrow-btn :deep(.el-icon) { font-size: 20px; font-weight: 700; }
.arrow-btn:hover:not(:disabled) { background: rgba(128,128,128,0.22); color: #1a2a4a; }
.arrow-btn:disabled { opacity: 0.25; cursor: not-allowed; }
.scroll-row { display: flex; gap: 14px; overflow-x: auto; overflow-y: hidden; scroll-behavior: smooth; padding-bottom: 6px; scrollbar-width: none; -ms-overflow-style: none; }
.scroll-row::-webkit-scrollbar { width: 0 !important; height: 0 !important; display: none !important; background: transparent; }
.scroll-card { flex: 0 0 170px; width: 170px; }
.scroll-loading { display: flex; gap: 14px; }
.scroll-empty { width: 100%; display: flex; justify-content: center; padding: 20px 0; }
@media (max-width: 900px) { .home-layout { flex-direction: column; overflow-y: auto; } .main-content { overflow-y: visible; } .sidebar { width: 100%; order: -1; overflow-y: visible; } }
@media (max-width: 768px) { .home-page { padding: 0 10px; } .scroll-card { flex: 0 0 130px; width: 130px; } .section-title { font-size: 15px; } }
</style>
