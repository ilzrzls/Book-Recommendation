<template>
  <div class="book-detail-page" v-loading="loading">
    <template v-if="book">
      <div class="detail-layout">
        <!-- Left: Cover & Basic Info -->
        <div class="left-section">
          <div class="cover-wrapper">
            <img :src="book.cover" :alt="book.title" class="detail-cover" />
          </div>
          <div class="book-meta">
            <h1 class="book-title">{{ book.title }}</h1>
            <p class="book-subtitle" v-if="book.subtitle">{{ book.subtitle }}</p>
            <div class="authors">
              <span v-for="author in book.authors" :key="author.id" class="author-name">
                {{ author.name }}
              </span>
            </div>
            <p class="meta-item" v-if="book.publisher">
              <span class="label">出版社：</span>{{ book.publisher.name }}
            </p>
            <p class="meta-item" v-if="book.publish_date">
              <span class="label">出版日期：</span>{{ book.publish_date }}
            </p>
            <p class="meta-item"><span class="label">页数：</span>{{ book.pages }}页</p>
            <p class="meta-item" v-if="book.isbn"><span class="label">ISBN：</span>{{ book.isbn }}</p>
            <p class="meta-item"><span class="label">定价：</span>&yen;{{ book.price }}</p>
          </div>

        </div>

        <!-- Right: Actions & Details -->
        <div class="right-section">
          <!-- Shelf Buttons -->
          <div class="action-buttons">
            <el-button
              v-for="s in shelfOptions"
              :key="s.type"
              :type="currentShelfType === s.type ? 'primary' : 'default'"
              :loading="addingShelf === s.type"
              @click="handleAddToShelf(s.type)"
            >
              <el-icon><component :is="s.icon" /></el-icon>
              {{ s.label }}
            </el-button>
            <el-button
              :type="currentShelfType ? 'success' : 'warning'"
              :plain="!currentShelfType"
              @click="openShelfPicker"
            >
              <el-icon><Star /></el-icon>
              {{ currentShelfType ? '已收藏' : '收藏至书架' }}
            </el-button>
          </div>

          <!-- AI Recommendation Reason -->
          <div class="reason-box">
            <h4><el-icon><MagicStick /></el-icon> 推荐理由</h4>
            <p>{{ recommendReason }}</p>
          </div>

          <!-- Rating & Tags -->
          <div class="rating-section">
            <div class="rating-score">{{ book.rating }}</div>
            <div>
              <el-rate :model-value="book.rating / 2" disabled size="large" />
              <p class="rating-count-text">{{ formatCount(book.rating_count) }} 人评分</p>
            </div>
          </div>
          <div class="tags-section">
            <el-tag v-for="tag in book.tags" :key="tag.id" type="warning" effect="plain" class="book-tag">
              {{ tag.name }}
            </el-tag>
          </div>

          <!-- Read Sample -->
          <div class="action-box">
            <el-button type="info" plain @click="handlePreview">
              <el-icon><Reading /></el-icon> {{ previewBtnText }}
            </el-button>
          </div>

          <!-- Buy Links -->
          <div class="action-box">
            <el-dropdown @command="handleBuy">
              <el-button type="success" plain>
                <el-icon><ShoppingCart /></el-icon> 购买实体书
                <el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="jd">京东</el-dropdown-item>
                  <el-dropdown-item command="dd">当当</el-dropdown-item>
                  <el-dropdown-item command="tb">淘宝</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

          <!-- Book Stats (豆瓣数据) -->
          <div class="stats-box">
            <span>{{ formatCount(book.want_count) }} 人想读</span>
            <span class="divider">|</span>
            <span>{{ formatCount(book.reading_count) }} 人在读</span>
            <span class="divider">|</span>
            <span>{{ formatCount(book.read_count) }} 人读过</span>
          </div>
        </div>
      </div>

      <!-- Summary -->
      <div class="summary-section">
        <h3>内容简介</h3>
        <p>{{ book.summary }}</p>
      </div>

      <!-- Similar Books -->
      <div class="similar-section" v-if="similarBooks.length">
        <h3>相似图书推荐</h3>
        <div class="similar-grid">
          <BookCard v-for="b in similarBooks" :key="b.id" :book="b" />
        </div>
      </div>

      <!-- Comments -->
      <CommentSection :book-id="book.id" />
    </template>

    <!-- 404 -->
    <el-result v-else-if="!loading" icon="warning" title="图书不存在" sub-title="请检查图书ID是否正确">
      <template #extra>
        <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
      </template>
    </el-result>

    <!-- Rating dialog: 标记"已读"后弹出 -->
    <el-dialog v-model="showRating" title="为本书评分" width="400px">
      <div style="text-align:center">
        <p style="margin-bottom:16px;color:#666">你刚将《{{ book?.title }}》标记为已读，给它打个分吧！</p>
        <el-rate v-model="ratingScore" :max="5" :step="0.5" allow-half size="large" :texts="['很差','较差','还行','推荐','力荐']" />
        <p style="margin-top:4px;font-size:13px;color:#D4A24C" v-if="ratingScore">{{ ratingScore }} 星 = {{ ratingScore * 2 }} 分（满分10分）</p>
      </div>
      <template #footer>
        <el-button @click="showRating = false">跳过</el-button>
        <el-button type="primary" :disabled="!ratingScore" :loading="ratingSubmitting" @click="submitRating">提交评分</el-button>
      </template>
    </el-dialog>

    <!-- Shelf picker dialog (outside v-if to avoid breaking chain) -->
    <el-dialog v-model="shelfPickerVisible" title="收藏到书架" width="440px">
      <p class="picker-book-name">{{ book?.title }}</p>
      <el-radio-group v-model="pickerSelectedShelf" class="picker-options">
        <el-radio
          v-for="s in allShelves"
          :key="s.id"
          :value="s.type"
          size="large"
          :disabled="s.type === currentShelfType"
        >
          <span>{{ s.name }}</span>
          <span class="picker-count">（{{ s.items.length }} 本）</span>
          <el-tag v-if="s.type === currentShelfType" size="small" type="info">已在其中</el-tag>
        </el-radio>
      </el-radio-group>
      <template #footer>
        <el-button @click="shelfPickerVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!pickerSelectedShelf" :loading="pickerAdding" @click="confirmShelfPicker">
          确定收藏
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBookStore } from '../stores/book'
import { useUserStore } from '../stores/user'
import { shelvesAPI } from '../api/shelves'
import { ElMessage } from 'element-plus'
import request from '../api/request'
import BookCard from '../components/common/BookCard.vue'
import CommentSection from '../components/book/CommentSection.vue'

const route = useRoute()
const router = useRouter()
const bookStore = useBookStore()
const userStore = useUserStore()

const book = computed(() => bookStore.currentBook)
const similarBooks = computed(() => bookStore.similarBooks)
const loading = computed(() => bookStore.loading)
const currentShelfType = ref('')
const addingShelf = ref('')  // Which shelf button is currently loading

const shelfOptions = [
  { type: 'want_read', label: '想读', icon: 'Bookmark' },
  { type: 'reading', label: '在读', icon: 'Reading' },
  { type: 'read', label: '已读', icon: 'Check' },
]

// ---- Shelf picker dialog state ----
const shelfPickerVisible = ref(false)
const pickerSelectedShelf = ref('')
const pickerAdding = ref(false)
const allShelves = ref([])

// 推荐理由：交叉验证用户书架 → 同作者须用户确实读过该作家的书
const recommendReason = ref('')
const reasonLoading = ref(false)

async function loadRecommendReason() {
  if (!book.value) return
  reasonLoading.value = true
  try {
    const title = book.value.title
    const author = book.value.author
    const score = book.value.rating
    const tags = (book.value.tags || []).map(t => t.name)
    const count = book.value.rating_count || 0

    // ── 已读/在读/想读 → 针对性文案 ──
    if (userStore.isLoggedIn) {
      const shelfType = currentShelfType.value
      if (shelfType === 'read') {
        // 获取同作者其他书
        let otherBooks = ''
        try {
          const simRes = await request.get(`/books/${book.value.id}/similar`)
          if (simRes.code === 200) {
            const sameAuthor = simRes.data.items?.filter(r => r.reason?.includes('同作者'))?.slice(0, 3)
            if (sameAuthor.length) {
              otherBooks = 'TA 还有《' + sameAuthor.map(s => s.title).join('》《') + '》等作品，不妨一读。'
            }
          }
        } catch {}
        recommendReason.value = `你已读完《${title}》。${otherBooks || '豆瓣 ' + count.toLocaleString() + ' 人评分 ' + score + '，是值得回味的经典。'}`
        reasonLoading.value = false; return
      }
      if (shelfType === 'reading') {
        recommendReason.value = `你正在读《${title}》。${author} 的笔触细腻，${tags.length ? '涵盖 ' + tags.slice(0,2).join('、') + ' 等主题，' : ''}祝你阅读愉快。`
        reasonLoading.value = false; return
      }
      if (shelfType === 'want_read') {
        recommendReason.value = `《${title}》在你的想读书单中。豆瓣 ${count.toLocaleString()} 人评分 ${score}，${score >= 9 ? '这是一部被广泛认可的经典' : score >= 8.5 ? '广受好评' : '值得期待'}。`
        reasonLoading.value = false; return
      }
    }

    // 获取用户的个性化数据
    let userAuthors = []   // 用户读过的作者
    let userTags = []      // 用户偏好标签
    if (userStore.isLoggedIn) {
      try {
        const shelfRes = await shelvesAPI.getShelves()
        if (shelfRes.code === 200) {
          const shelves = shelfRes.data.shelves
          // 收集所有书架中的作者
          const authorSet = new Set()
          const tagSet = new Set()
          for (const sh of shelves) {
            for (const it of (sh.items || [])) {
              if (it.book?.author) authorSet.add(it.book.author)
            }
          }
          userAuthors = [...authorSet]
          // 从 profile 获取标签
          try {
            const pRes = await request.get('/auth/profile')
            if (pRes.code === 200 && pRes.data?.reading_stats?.tag_distribution) {
              userTags = pRes.data.reading_stats.tag_distribution.map(t => t.name)
            }
          } catch {}
        }
      } catch {}
    }

    // ── 生成推荐理由 ──
    // 策略1: 用户读过该作家的书 → 同作者推荐
    if (userAuthors.includes(author)) {
      recommendReason.value = `你读过 ${author} 的作品，而《${title}》是 TA 的又一力作。${score >= 9 ? '这本书在豆瓣上评分极高，' : ''}${tags.length > 0 ? '涵盖 ' + tags.slice(0,3).join('、') + ' 等主题，' : ''}延续了 TA 一贯的叙事风格。`
      reasonLoading.value = false
      return
    }

    // 策略2: 用户偏好标签与本书标签有交集
    const sharedTags = userTags.filter(t => tags.includes(t))
    if (sharedTags.length >= 2) {
      recommendReason.value = `你偏爱「${sharedTags.slice(0,2).join('」和「')}」类作品，《${title}》正好同时涵盖这些主题。豆瓣 ${count.toLocaleString()} 人评分 ${score}，与你的阅读口味高度契合。`
      reasonLoading.value = false
      return
    }

    // 策略3: 获取相似书 KG 路径 → 只取标签/出版社理由，排除同作者
    if (userStore.isLoggedIn) {
      try {
        const res = await request.get(`/books/${book.value.id}/similar`)
        if (res.code === 200 && res.data.items?.length > 0) {
          const tagReasons = res.data.items
            .map(r => r.reason)
            .filter(Boolean)
            .filter(r => r.includes('同标签') || r.includes('同出版社'))
          if (tagReasons.length > 0) {
            const best = tagReasons[0]
            if (best.includes('同标签')) {
              const t = best.replace(/同标签[:：]\s*/, '').trim()
              recommendReason.value = `《${title}》属于「${t}」类作品，豆瓣评分 ${score}，${score >= 9 ? '经典不容错过' : '广受好评'}。${count > 10000 ? '超 ' + Math.round(count/10000) + ' 万人评价，' : ''}在同类作品中表现突出。`
            } else {
              const p = best.replace(/同出版社[:：]\s*/, '').trim()
              recommendReason.value = `由「${p}」出版，品质有保障。豆瓣评分 ${score}，${count.toLocaleString()} 人评价。`
            }
            reasonLoading.value = false
            return
          }
        }
      } catch {}
    }

    // 策略4: 通用品质推荐（未登录或无匹配）
    const tagStr = tags.slice(0, 3).join('、')
    recommendReason.value = tagStr
      ? `《${title}》涵盖 ${tagStr} 等主题，豆瓣 ${count.toLocaleString()} 人评分 ${score}，${score >= 9 ? '是当之无愧的经典之作' : score >= 8.5 ? '广受读者好评' : '值得一读'}。`
      : `${author} 的代表作之一，豆瓣 ${count.toLocaleString()} 人打出 ${score} 分。${score >= 9 ? '经典不容错过。' : '值得细细品读。'}`
  } catch {
    recommendReason.value = ''
  }
  reasonLoading.value = false
}

async function loadBook(id) {
  if (!id) return
  await Promise.all([
    bookStore.fetchBookDetail(id),
    bookStore.fetchSimilarBooks(id),
  ])
  // 游客不调用户专属API，避免401触发登录跳转
  if (userStore.isLoggedIn) {
    await detectShelfStatus(id)
  }
  loadRecommendReason()
  checkChapters()
}

onMounted(() => loadBook(Number(route.params.id)))

// 监听路由参数变化：从书A跳转到书B时重新加载数据
watch(() => route.params.id, (newId) => loadBook(Number(newId)))

// 检测图书是否已在书架中
async function detectShelfStatus(bookId) {
  try {
    const res = await shelvesAPI.getShelves()
    if (res.code === 200) {
      const shelves = res.data.shelves
      for (const shelf of shelves) {
        const found = shelf.items?.some(it => it.book?.id === bookId)
        if (found) {
          currentShelfType.value = shelf.type
          break
        }
      }
    }
  } catch (e) { /* ignore */ }
}

// 想读/在读/已读 — 切换状态：点一次设置，再点一次取消
async function handleAddToShelf(shelfType) {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  addingShelf.value = shelfType
  try {
    if (currentShelfType.value === shelfType) {
      // 已在该状态 → 取消（从书架移除）
      await shelvesAPI.removeBook(book.value.id)
      currentShelfType.value = ''
      ElMessage.success('已取消标记')
    } else {
      // 切换到新状态
      const res = await shelvesAPI.addItem(book.value.id, shelfType)
      if (res.code === 200) {
        const prevType = currentShelfType.value
        currentShelfType.value = shelfType
        ElMessage.success(`已标记为「${res.data.shelf_name}」`)
        // 标记为"已读"后弹出评分
        if (shelfType === 'read' && prevType !== 'read') {
          showRating.value = true
        }
      }
    }
  } finally {
    addingShelf.value = ''
  }
}

// ── 评分 ──
const showRating = ref(false)
const ratingScore = ref(0)
const ratingSubmitting = ref(false)

async function submitRating() {
  if (!ratingScore.value) return
  ratingSubmitting.value = true
  try {
    const finalScore = ratingScore.value * 2  // 5星制 → 10分制
    await request.post('/user/rating', { book_id: book.value.id, score: finalScore })
    ElMessage.success(`已评分 ${finalScore} 分！个性化推荐将据此优化`)
    showRating.value = false
  } catch {
    ElMessage.error('评分失败')
  }
  ratingSubmitting.value = false
}

// 收藏至书架 — 打开书架选择弹窗
async function openShelfPicker() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  // 加载最新书架列表
  const res = await shelvesAPI.getShelves()
  if (res.code === 200) {
    allShelves.value = res.data.shelves
    // 默认选中第一个非当前的书架
    const other = allShelves.value.find(s => s.type !== currentShelfType.value)
    pickerSelectedShelf.value = other?.type || allShelves.value[0]?.type || ''
  }
  shelfPickerVisible.value = true
}

async function confirmShelfPicker() {
  if (!pickerSelectedShelf.value) return
  pickerAdding.value = true
  try {
    const res = await shelvesAPI.addItem(book.value.id, pickerSelectedShelf.value)
    if (res.code === 200) {
      currentShelfType.value = pickerSelectedShelf.value
      ElMessage.success(`已收藏到「${res.data.shelf_name}」`)
    }
  } finally {
    pickerAdding.value = false
    shelfPickerVisible.value = false
  }
}

const hasChapters = ref(false)
const previewBtnText = computed(() => {
  if (hasChapters.value) return userStore.isLoggedIn ? '阅读整本' : '试读10页'
  return '前往试读'
})

async function checkChapters() {
  const id = book.value?.id
  if (!id) return
  try {
    const res = await request.get(`/books/${id}/chapters`)
    hasChapters.value = res.code === 200 && res.data?.total > 0
  } catch { hasChapters.value = false }
}

async function handlePreview() {
  const id = book.value?.id
  if (!id) return
  if (hasChapters.value) {
    router.push(`/read/${id}`)
    return
  }
  const title = book.value?.title
  if (title) {
    window.open(`https://read.douban.com/search?q=${encodeURIComponent(title)}`, '_blank')
  }
}

function handleBuy(platform) {
  const urls = {
    jd: 'https://search.jd.com/Search?keyword=',
    dd: 'https://search.dangdang.com/?key=',
    tb: 'https://s.taobao.com/search?q=',
  }
  // TODO: 后续替换为真实购书链接
  window.open(urls[platform] + encodeURIComponent(book.value.title), '_blank')
}

function formatCount(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n.toString()
}
</script>

<style scoped>
.book-detail-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.detail-layout {
  display: flex;
  gap: 40px;
  margin-bottom: 30px;
}

.left-section {
  width: 320px;
  flex-shrink: 0;
}

.cover-wrapper {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
  margin-bottom: 20px;
}
.detail-cover {
  width: 100%;
  aspect-ratio: 3/4;
  object-fit: cover;
  display: block;
}

.book-title {
  font-size: 22px;
  color: #2C3E50;
  margin-bottom: 4px;
}
.book-subtitle {
  font-size: 14px;
  color: #888;
  margin-bottom: 8px;
}
.authors {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.author-name {
  color: #D4A24C;
  font-size: 14px;
}
.meta-item {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}
.meta-item .label {
  color: #999;
}

.rating-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
  padding: 12px;
  background: #FFF8E7;
  border-radius: 8px;
}
.rating-score {
  font-size: 36px;
  font-weight: bold;
  color: #D4A24C;
}
.rating-count-text {
  font-size: 12px;
  color: #aaa;
  margin-top: 4px;
}

.tags-section {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.right-section {
  flex: 1;
}

.action-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.reason-box {
  background: linear-gradient(135deg, #FFF8E7, #FFFDF5);
  border-left: 4px solid #D4A24C;
  padding: 16px;
  border-radius: 0 8px 8px 0;
  margin-bottom: 16px;
}
.reason-box h4 {
  color: #D4A24C;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.reason-box p {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
}

.action-box {
  margin-bottom: 12px;
}

.progress-box {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
}
.progress-box h4 {
  font-size: 14px; color: #2C3E50;
  display: flex; align-items: center; gap: 6px;
  margin: 0 0 12px;
}
.progress-row {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 12px;
}
.progress-label { font-size: 13px; color: #666; }
.progress-pct { font-size: 18px; font-weight: bold; color: #D4A24C; margin-left: auto; }

.stats-box {
  font-size: 13px;
  color: #999;
  margin-top: 16px;
}
.divider {
  margin: 0 8px;
}

.summary-section {
  margin-bottom: 30px;
}
.summary-section h3 {
  font-size: 18px;
  color: #2C3E50;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #D4A24C;
}
.summary-section p {
  font-size: 14px;
  color: #555;
  line-height: 1.8;
  text-indent: 2em;
}

.similar-section h3 {
  font-size: 18px;
  color: #2C3E50;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #D4A24C;
}
.similar-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
  margin-bottom: 30px;
}

/* ---- Shelf picker dialog ---- */
.picker-book-name {
  font-size: 16px;
  font-weight: 600;
  color: #2C3E50;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.picker-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.picker-options .el-radio {
  margin-right: 0;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid transparent;
  transition: all 0.2s;
  width: 100%;
}
.picker-options .el-radio:hover {
  background: #F8F9FA;
  border-color: #D4A24C;
}

.picker-count {
  color: #999;
  font-size: 13px;
  margin-left: 4px;
}

@media (max-width: 768px) {
  .detail-layout {
    flex-direction: column;
  }
  .left-section {
    width: 100%;
    max-width: 280px;
    margin: 0 auto;
  }
}
</style>
