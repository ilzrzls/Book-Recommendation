<template>
  <div class="graph-search-page">
    <div class="gs-header">
      <h2>📊 知识图谱探索</h2>
      <p class="gs-subtitle">通过标签筛选或自由搜索，探索图书关联关系</p>
    </div>

    <!-- 模式切换 -->
    <div class="mode-switch-row">
      <span class="mode-tab" :class="{ active: searchMode === 'filter' }"
            @click="switchMode('filter')">🏷️ 标签筛选</span>
      <span class="mode-tab" :class="{ active: searchMode === 'free' }"
            @click="switchMode('free')">🔎 自由搜索</span>
    </div>

    <!-- ==================== 标签筛选模式 ==================== -->
    <div v-if="searchMode === 'filter'" class="filter-panel">
      <!-- 价格 -->
      <div class="filter-section">
        <span class="filter-section-title">价格</span>
        <div class="filter-price-tags">
          <span class="price-tag" :class="{ active: filterPrice === 'free' }"
                @click="toggleFilterPrice('free')">免费</span>
          <span class="price-tag" :class="{ active: filterPrice === 'paid' }"
                @click="toggleFilterPrice('paid')">付费</span>
        </div>
      </div>

      <!-- 题材标签（多选） -->
      <div class="filter-section">
        <div class="filter-section-header">
          <span class="filter-section-title">题材（可多选）</span>
          <el-button size="small" text @click="selectedGenreTags = []">清空</el-button>
        </div>
        <div class="filter-tags">
          <el-check-tag v-for="tag in allTags" :key="tag.id"
            :checked="selectedGenreTags.includes(tag.name)"
            @change="(c) => toggleGenreTag(tag.name, c)" size="small">
            {{ tag.name }}
          </el-check-tag>
        </div>
      </div>

      <!-- 作家标签（多选） -->
      <div class="filter-section">
        <div class="filter-section-header">
          <span class="filter-section-title">作家（可多选）</span>
          <el-button size="small" text @click="selectedAuthorTags = []">清空</el-button>
        </div>
        <div class="filter-tags author-tags">
          <el-check-tag v-for="author in allAuthors" :key="author.id"
            :checked="selectedAuthorTags.includes(author.name)"
            @change="(c) => toggleAuthorTag(author.name, c)" size="small">
            {{ author.name }}
          </el-check-tag>
        </div>
      </div>

      <!-- 操作行 -->
      <div class="filter-actions-row">
        <div class="filter-depth-toggle">
          <span class="filter-depth-label">关联深度：</span>
          <span class="depth-btn" :class="{ active: filterDepth === 1 }"
                @click="filterDepth = 1">一级</span>
          <span class="depth-btn" :class="{ active: filterDepth === 2 }"
                @click="filterDepth = 2">二级</span>
        </div>
        <div v-if="activeFilterSummary" class="filter-summary">
          🔍 筛选：<strong>{{ activeFilterSummary }}</strong>
        </div>
        <div class="filter-buttons">
          <el-button size="small" text @click="clearAllFilters">清空全部</el-button>
          <el-button size="small" type="primary" @click="applyFilterGraph"
            :disabled="!filterPrice && selectedGenreTags.length === 0 && selectedAuthorTags.length === 0">
            生成图谱
          </el-button>
        </div>
      </div>
    </div>

    <!-- ==================== 自由搜索模式 ==================== -->
    <div v-if="searchMode === 'free'" class="gs-search-row">
      <div class="gs-search-wrap" ref="searchWrapRef">
        <el-input v-model="searchKeyword" placeholder="搜索图书、作者或标签..." size="large"
          clearable @focus="onSearchFocus" @input="onSearchInput" @clear="onSearchClear">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <div class="gs-dropdown" v-if="showDropdown && hotItems.length" @mousedown.prevent>
          <div class="hot-tags-wrap">
            <span class="hot-tag-item" :class="item.type" v-for="item in hotItems"
                  :key="item.type+item.name" @click="selectEntity(item.type, { name: item.name })">
              {{ item.type === 'author' ? '✍️' : '🏷️' }} {{ item.name }}
            </span>
          </div>
        </div>
        <div class="gs-dropdown" v-else-if="showDropdown && hasSearchResults" @mousedown.prevent>
          <div class="result-group" v-if="searchResults.books?.length">
            <div class="group-title">📕 图书</div>
            <div class="result-item" v-for="item in searchResults.books" :key="'b'+item.book_id"
                 @click="selectEntity('book', item)">
              <span>{{ item.title }}</span><span class="item-extra">★ {{ item.score?.toFixed(1) || '?' }}</span>
            </div>
          </div>
          <div class="result-group" v-if="searchResults.authors?.length">
            <div class="group-title">✍️ 作者</div>
            <div class="result-item" v-for="item in searchResults.authors" :key="'a'+item.author_id"
                 @click="selectEntity('author', item)"><span>{{ item.name }}</span></div>
          </div>
          <div class="result-group" v-if="searchResults.tags?.length">
            <div class="group-title">🏷️ 标签</div>
            <div class="result-item" v-for="item in searchResults.tags" :key="'t'+item.tag_id"
                 @click="selectEntity('tag', item)"><span>{{ item.name }}</span></div>
          </div>
        </div>
      </div>

      <!-- 自由搜索统计+深度 -->
      <div class="gs-toolbar">
        <span class="depth-toggle" v-if="hasGraph">
          <span class="depth-label">关联深度：</span>
          <span class="depth-btn" :class="{ active: exploreDepth === 1 }" @click="setDepth(1)">一级</span>
          <span class="depth-btn" :class="{ active: exploreDepth === 2 }" @click="setDepth(2)">二级</span>
        </span>
        <div class="graph-stats" v-if="hasGraph">
          <span class="stat-item book">图书 {{ nodeCounts.book }}</span>
          <span class="stat-item author">作者 {{ nodeCounts.author }}</span>
          <span class="stat-item tag">标签 {{ nodeCounts.tag }}</span>
        </div>
      </div>

      <div class="gs-current" v-if="currentEntity">
        <span>当前：<strong>{{ currentEntity.name }}</strong></span>
        <el-button size="small" @click="clearNetwork">清空</el-button>
      </div>
    </div>

    <!-- 筛选结果消息 -->
    <div v-if="filterMessage" class="filter-status" :class="{ 'filter-empty': filterTotal === 0 }">
      {{ filterMessage }}
    </div>

    <!-- ==================== 图谱区域 ==================== -->
    <div v-if="graphLoading" class="gs-chart-wrap" style="display:flex;align-items:center;justify-content:center;">
      <el-icon :size="40" class="is-loading"><Loading /></el-icon>
      <span style="margin-left:12px;color:#999;">生成图谱中...</span>
    </div>

    <div v-else-if="!filterActive && !hasGraph" class="gs-chart-wrap gs-placeholder">
      <div class="placeholder-content">
        <el-icon :size="48" color="#D4A24C"><Search /></el-icon>
        <p v-if="searchMode === 'filter'">选择标签后点击"生成图谱"</p>
        <p v-else>搜索图书、作者或标签开始探索</p>
      </div>
    </div>

    <div v-else ref="chartRef" class="gs-chart-wrap"></div>

    <!-- 图例 -->
    <div class="gs-legend" v-if="hasGraph">
      <span class="legend-item"><span class="legend-dot" style="background:#D4A24C"></span>图书（点击进入详情）</span>
      <span class="legend-item"><span class="legend-dot" style="background:#3498DB"></span>作者（点击展开）</span>
      <span class="legend-item"><span class="legend-dot" style="background:#2ECC71"></span>标签（点击展开）</span>
      <span class="legend-hint">🖱️ 滚轮缩放 | 拖拽移动</span>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import request from '../api/request'
import * as echarts from 'echarts'

const router = useRouter()
const chartRef = ref(null)
const searchWrapRef = ref(null)

// ── 模式 ──
const searchMode = ref('filter')

function switchMode(mode) {
  searchMode.value = mode
  if (mode === 'free') {
    clearAllFilters()
    currentEntity.value = null
  }
}

// ═══════ 标签筛选模式 ═══════
const allTags = ref([])
const allAuthors = ref([])
const selectedGenreTags = ref([])
const selectedAuthorTags = ref([])
const filterPrice = ref('')
const filterDepth = ref(1)
const filterActive = ref(false)
const filterTotal = ref(0)
const filterMessage = ref('')
const graphLoading = ref(false)
let savedFilterGraphData = null

const activeFilterSummary = computed(() => {
  const parts = []
  if (filterPrice.value === 'free') parts.push('免费')
  else if (filterPrice.value === 'paid') parts.push('付费')
  if (selectedGenreTags.value.length) parts.push(selectedGenreTags.value.join(' + '))
  if (selectedAuthorTags.value.length) parts.push(selectedAuthorTags.value.join(' + '))
  return parts.join('、')
})

function toggleFilterPrice(type) {
  filterPrice.value = filterPrice.value === type ? '' : type
}
function toggleGenreTag(name, checked) {
  if (checked) selectedGenreTags.value.push(name)
  else selectedGenreTags.value = selectedGenreTags.value.filter(t => t !== name)
}
function toggleAuthorTag(name, checked) {
  if (checked) selectedAuthorTags.value.push(name)
  else selectedAuthorTags.value = selectedAuthorTags.value.filter(t => t !== name)
}

function clearAllFilters() {
  selectedGenreTags.value = []
  selectedAuthorTags.value = []
  filterPrice.value = ''
  filterDepth.value = 1
  filterActive.value = false
  filterTotal.value = 0
  filterMessage.value = ''
  nodeCounts.book = 0; nodeCounts.author = 0; nodeCounts.tag = 0
  savedFilterGraphData = null
  graphNodes = []
  graphLinks = []
  currentEntity.value = null
  if (chartInstance) { chartInstance.dispose(); chartInstance = null }
}

async function applyFilterGraph() {
  const params = {}
  if (selectedGenreTags.value.length) params.tags = selectedGenreTags.value.join(',')
  if (selectedAuthorTags.value.length) params.authors = selectedAuthorTags.value.join(',')
  if (filterPrice.value) params.price = filterPrice.value
  params.limit = 30
  params.depth = filterDepth.value

  graphLoading.value = true
  filterActive.value = true
  currentEntity.value = null
  try {
    const res = await request.get('/graph/filter', { params })
    if (res.code === 200) {
      const d = res.data
      filterTotal.value = d.total || 0
      filterMessage.value = d.message || ''
      categories = d.categories || []
      savedFilterGraphData = d
      if (d.nodes && d.nodes.length > 0) {
        renderNetwork(d)
      } else {
        nodeCounts.book = 0; nodeCounts.author = 0; nodeCounts.tag = 0
        if (chartInstance) { chartInstance.dispose(); chartInstance = null }
      }
    }
  } catch { /* ignore */ }
  graphLoading.value = false
}

// 深度变化时自动重新生成图谱（避免用户点击深度后还需手动点"生成图谱"）
watch(filterDepth, () => {
  if (filterActive.value) applyFilterGraph()
})

// ═══════ 自由搜索模式 ═══════
const searchKeyword = ref('')
const showDropdown = ref(false)
const hotItems = ref([])
const searchResults = ref({ books: [], authors: [], tags: [] })
const hasSearchResults = computed(() =>
  (searchResults.value.books?.length || 0) > 0 ||
  (searchResults.value.authors?.length || 0) > 0 ||
  (searchResults.value.tags?.length || 0) > 0
)
const currentEntity = ref(null)
const exploreDepth = ref(1)
let searchTimer = null

async function callGraphAPI(params = {}) {
  return request.get('/graph/search', { params })
}

async function onSearchFocus() {
  if (searchKeyword.value && searchKeyword.value.trim()) return
  showDropdown.value = true
  try {
    const graphRes = await callGraphAPI().catch(() => null)
    const items = []
    if (graphRes?.data?.node_stats) {
      const tagNodes = (graphRes.data.nodes || []).filter(n => n.category === 'tag').slice(0, 6)
      tagNodes.forEach(t => items.push({ name: t.name, type: 'tag' }))
      const authorNodes = (graphRes.data.nodes || []).filter(n => n.category === 'author').slice(0, 4)
      authorNodes.forEach(a => items.push({ name: a.name, type: 'author' }))
    }
    hotItems.value = items.slice(0, 10)
  } catch { hotItems.value = [] }
}

async function onSearchInput() {
  const kw = searchKeyword.value.trim()
  if (!kw) { showDropdown.value = false; searchResults.value = { books: [], authors: [], tags: [] }; return }
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    try {
      const res = await callGraphAPI({ keyword: kw })
      if (res.code === 200 && res.data.type === 'search_results') {
        searchResults.value = { books: res.data.books || [], authors: res.data.authors || [], tags: res.data.tags || [] }
        hotItems.value = []
        showDropdown.value = true
      }
    } catch { /* ignore */ }
  }, 250)
}

function onSearchClear() {
  showDropdown.value = false
  searchResults.value = { books: [], authors: [], tags: [] }
  hotItems.value = []
}

function selectEntity(type, item) {
  showDropdown.value = false
  searchKeyword.value = ''
  searchResults.value = { books: [], authors: [], tags: [] }
  hotItems.value = []
  currentEntity.value = { type, name: item.title || item.name }
  const params = {}
  if (type === 'book') params.book_id = item.book_id
  else if (type === 'author') params.author = item.name
  else if (type === 'tag') params.tag = item.name
  loadEgoNetwork(params)
}

async function loadEgoNetwork(params = {}) {
  graphLoading.value = true
  try {
    const res = await callGraphAPI({ ...params, depth: exploreDepth.value })
    if (res.code === 200 && res.data.nodes?.length) {
      renderNetwork(res.data)
    }
  } catch { /* ignore */ }
  graphLoading.value = false
}

async function loadInitialGraph() {
  graphLoading.value = true
  try {
    const res = await callGraphAPI()
    if (res.code === 200) {
      const d = res.data
      categories = d.categories || []
      if (d.type === 'top10_overview') {
        nodeCounts.book = d.node_stats?.book || 0
        nodeCounts.author = d.node_stats?.author || 0
        nodeCounts.tag = d.node_stats?.tag || 0
        renderNetwork(d)
      }
    }
  } catch { /* ignore */ }
  graphLoading.value = false
}

function clearNetwork() {
  currentEntity.value = null
  exploreDepth.value = 1
  loadInitialGraph()
}

// 自由搜索深度变化 → 自动重查
watch(exploreDepth, () => {
  if (searchMode.value === 'free' && currentEntity.value) {
    const params = {}
    if (currentEntity.value.type === 'author') params.author = currentEntity.value.name
    else if (currentEntity.value.type === 'tag') params.tag = currentEntity.value.name
    loadEgoNetwork(params)
  }
})

function setDepth(d) {
  if (exploreDepth.value === d) return
  exploreDepth.value = d
  if (currentEntity.value) {
    const params = {}
    if (currentEntity.value.type === 'author') params.author = currentEntity.value.name
    else if (currentEntity.value.type === 'tag') params.tag = currentEntity.value.name
    loadEgoNetwork(params)
  }
}

// ═══════ 图谱渲染（共享） ═══════
const nodeCounts = reactive({ book: 0, author: 0, tag: 0 })
const hasGraph = computed(() => nodeCounts.book > 0 || nodeCounts.author > 0 || nodeCounts.tag > 0)

let chartInstance = null
let graphNodes = []
let graphLinks = []
let categories = []

function renderNetwork(d) {
  graphLinks = d.links || []
  categories = d.categories || []

  const engToCh = { book: '图书', author: '作者', tag: '标签' }
  const chToIdx = {}
  ;(d.categories || []).forEach((c, i) => { chToIdx[c.name] = i })

  graphNodes = (d.nodes || []).map(n => ({
    ...n,
    category: chToIdx[engToCh[n.category]] ?? 0
  }))

  nodeCounts.book = graphNodes.filter(n => n.category === (chToIdx['图书'] ?? 0)).length
  nodeCounts.author = graphNodes.filter(n => n.category === (chToIdx['作者'] ?? 1)).length
  nodeCounts.tag = graphNodes.filter(n => n.category === (chToIdx['标签'] ?? 2)).length

  graphLoading.value = false
  nextTick(() => { setTimeout(() => initChart(), 150) })
}

function initChart() {
  if (!chartRef.value) return
  const el = chartRef.value
  if (el.offsetWidth === 0 || el.offsetHeight === 0) { setTimeout(initChart, 200); return }
  if (chartInstance) { chartInstance.dispose(); chartInstance = null }

  try {
    chartInstance = echarts.init(el)
    const catNameToIdx = {}
    ;(categories || []).forEach((c, i) => { catNameToIdx[c.name] = i })

    chartInstance.setOption({
      tooltip: {
        formatter: (p) => {
          if (p.dataType === 'edge') return p.data.label || ''
          const catNames = (categories || []).map(c => c.name)
          return `<b>${p.data.name}</b><br/>类型: ${catNames[p.data.category] || p.data.category}`
        },
      },
      animationDuration: 800,
      series: [{
        type: 'graph',
        layout: 'force',
        force: { repulsion: 400, edgeLength: [60, 180], gravity: 0.08, friction: 0.6 },
        roam: true,
        draggable: true,
        data: graphNodes,
        links: graphLinks,
        categories: categories,
        label: {
          show: true, position: 'right', fontSize: 11, color: '#555',
          formatter: p => { const name = p.data.name || ''; return name.length > 10 ? name.slice(0, 9) + '…' : name }
        },
        emphasis: { focus: 'adjacency', label: { fontSize: 14, fontWeight: 'bold' } },
        itemStyle: { borderColor: '#fff', borderWidth: 2 },
        lineStyle: { color: '#ccc', curveness: 0.2, opacity: 0.5 },
        edgeSymbol: ['none', 'none'],
        zoom: 1.2,
      }],
    })

    chartInstance.on('click', (params) => {
      if (params.dataType === 'node') {
        const node = params.data
        if (node.category === catNameToIdx['图书']) {
          if (node.mysql_id) router.push(`/book/${node.mysql_id}`)
        } else if (node.category === catNameToIdx['作者']) {
          currentEntity.value = { type: 'author', name: node.name }
          loadEgoNetwork({ author: node.name })
        } else if (node.category === catNameToIdx['标签']) {
          currentEntity.value = { type: 'tag', name: node.name }
          loadEgoNetwork({ tag: node.name })
        }
      }
    })
  } catch (e) { console.error('ECharts error:', e) }
}

// 点击外部关闭下拉
function onClickOutside(e) {
  if (searchWrapRef.value && !searchWrapRef.value.contains(e.target)) {
    showDropdown.value = false
  }
}

// ── 生命周期 ──
let resizeHandler
onMounted(async () => {
  // 加载筛选选项
  try {
    const optRes = await request.get('/graph/filter-options')
    if (optRes.code === 200) {
      allTags.value = optRes.data.tags || []
      allAuthors.value = optRes.data.authors || []
    }
  } catch { /* ignore */ }
  // 默认显示 Top10 图书图谱
  try {
    const graphRes = await callGraphAPI()
    if (graphRes.code === 200) {
      const d = graphRes.data
      categories = d.categories || []
      if (d.type === 'top10_overview' && d.nodes?.length) {
        nodeCounts.book = d.node_stats?.book || 0
        nodeCounts.author = d.node_stats?.author || 0
        nodeCounts.tag = d.node_stats?.tag || 0
        renderNetwork(d)
      }
    }
  } catch { /* ignore */ }
  resizeHandler = () => chartInstance?.resize()
  window.addEventListener('resize', resizeHandler)
  document.addEventListener('click', onClickOutside)
})
onBeforeUnmount(() => {
  chartInstance?.dispose()
  window.removeEventListener('resize', resizeHandler)
  document.removeEventListener('click', onClickOutside)
  if (searchTimer) clearTimeout(searchTimer)
})
</script>

<style scoped>
.graph-search-page { max-width: 1200px; margin: 0 auto; padding: 0; }
.gs-header { margin-bottom: 12px; }
.gs-header h2 { font-size: 22px; color: #2C3E50; margin: 0 0 4px; }
.gs-subtitle { color: #999; font-size: 13px; margin: 0; }

/* ── 模式切换 ── */
.mode-switch-row { display: flex; gap: 0; margin-bottom: 12px; }
.mode-tab {
  padding: 6px 18px; font-size: 13px; cursor: pointer; user-select: none;
  border: 1px solid #ddd; background: #fafafa; color: #888; transition: all 0.2s;
}
.mode-tab:first-child { border-radius: 8px 0 0 8px; }
.mode-tab:last-child { border-radius: 0 8px 8px 0; }
.mode-tab.active { background: #D4A24C; border-color: #D4A24C; color: #fff; }

/* ── 筛选面板 ── */
.filter-panel {
  background: #fff; border-radius: 10px; padding: 14px 16px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06); margin-bottom: 12px;
}
.filter-section { margin-bottom: 10px; }
.filter-section:last-child { margin-bottom: 0; }
.filter-section-title { font-size: 13px; color: #666; font-weight: 600; margin-right: 10px; }
.filter-section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.filter-price-tags { display: flex; gap: 8px; margin-top: 4px; }
.price-tag {
  padding: 4px 14px; border-radius: 14px; font-size: 13px; cursor: pointer;
  border: 1px solid #d9d9d9; background: #fafafa; transition: all 0.2s; user-select: none;
}
.price-tag:hover { border-color: #D4A24C; color: #D4A24C; }
.price-tag.active { background: #D4A24C; border-color: #D4A24C; color: #fff; }
.filter-tags { display: flex; flex-wrap: wrap; gap: 6px; max-height: 180px; overflow-y: auto; }
.filter-tags.author-tags { max-height: 150px; }

.filter-actions-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-top: 4px; }
.filter-depth-toggle { display: flex; align-items: center; gap: 4px; font-size: 13px; }
.filter-depth-label { color: #888; }
.depth-btn {
  padding: 3px 12px; border-radius: 12px; cursor: pointer; background: #f5f5f5;
  color: #666; transition: all 0.2s; font-size: 12px; border: 1px solid #e0e0e0; user-select: none;
}
.depth-btn.active { background: #D4A24C; color: #fff; border-color: #D4A24C; }
.filter-summary { font-size: 12px; color: #888; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.filter-buttons { display: flex; gap: 6px; margin-left: auto; }

.filter-status { font-size: 13px; color: #D4A24C; margin-bottom: 8px; padding: 4px 10px; background: #FFF8E7; border-radius: 6px; }
.filter-status.filter-empty { color: #e74c3c; background: #fdf0ef; }

/* ── 自由搜索 ── */
.gs-search-row { display: flex; align-items: flex-start; gap: 16px; margin-bottom: 12px; flex-wrap: wrap; }
.gs-search-wrap { position: relative; flex: 1; min-width: 280px; max-width: 520px; }
.gs-dropdown {
  position: absolute; top: 100%; left: 0; right: 0; z-index: 2000;
  background: #fff; border: 1px solid #e0e0e0; border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12); max-height: 380px; overflow-y: auto; margin-top: 4px;
}
.hot-tags-wrap { display: flex; flex-wrap: wrap; gap: 8px; padding: 12px; }
.hot-tag-item {
  padding: 5px 14px; border-radius: 16px; font-size: 13px; cursor: pointer;
  background: linear-gradient(135deg, #fef5e7, #fdf2e9); color: #D4A24C;
  border: 1px solid #f5d5a0; transition: all 0.2s;
}
.hot-tag-item:hover { transform: scale(1.05); }
.hot-tag-item.author {
  background: linear-gradient(135deg, #eef5fb, #e8f0fe); color: #3498DB; border: 1px solid #a0cff5;
}
.result-group { padding: 4px 0; }
.result-group + .result-group { border-top: 1px solid #f0f0f0; }
.group-title { padding: 6px 14px; font-size: 12px; color: #999; font-weight: 600; }
.result-item { display: flex; justify-content: space-between; align-items: center; padding: 7px 14px; cursor: pointer; transition: background 0.15s; }
.result-item:hover { background: #f5f7fa; }
.result-item span { font-size: 14px; color: #333; }
.item-extra { font-size: 12px; color: #aaa; }
.gs-toolbar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.depth-toggle { display: flex; align-items: center; gap: 4px; font-size: 13px; }
.depth-label { color: #888; }
.graph-stats { display: flex; align-items: center; gap: 8px; }
.stat-item { padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 500; }
.stat-item.book { color: #D4A24C; background: #FFF8E7; }
.stat-item.author { color: #3498DB; background: #EEF5FB; }
.stat-item.tag { color: #2ECC71; background: #E8F8F0; }
.gs-current { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; font-size: 13px; color: #666; }

/* ── 图谱 ── */
.gs-chart-wrap {
  width: 100%; height: 68vh; min-height: 500px;
  background: #fff; border-radius: 12px; overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}
.gs-placeholder { display: flex; align-items: center; justify-content: center; }
.placeholder-content { text-align: center; color: #999; }
.placeholder-content p { margin-top: 12px; font-size: 14px; }

.gs-legend { display: flex; align-items: center; gap: 16px; margin-top: 12px; font-size: 13px; color: #888; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 4px; }
.legend-dot { display: inline-block; width: 12px; height: 12px; border-radius: 50%; }
.legend-hint { margin-left: auto; font-size: 12px; color: #bbb; }

@media (max-width: 768px) {
  .gs-search-row { flex-direction: column; }
  .gs-search-wrap { max-width: 100%; }
  .filter-actions-row { flex-direction: column; align-items: flex-start; }
  .filter-buttons { margin-left: 0; }
}
</style>
