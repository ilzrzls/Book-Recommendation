<template>
  <div class="kg-page">
    <div class="page-header">
      <h2>📊 知识图谱可视化</h2>
    </div>

    <!-- 搜索栏 -->
    <div class="search-row">
      <div class="search-input-wrap" ref="searchWrapRef">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索图书、作者、出版社或标签..."
          size="large"
          clearable
          @focus="onSearchFocus"
          @input="onSearchInput"
          @clear="onSearchClear"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>

        <!-- 搜索下拉 -->
        <div class="search-results" v-if="showDropdown && hasResults" @mousedown.prevent>
          <!-- 图书 -->
          <div class="result-group" v-if="searchResults.books?.length">
            <div class="group-title">📕 图书</div>
            <div
              class="result-item"
              v-for="item in searchResults.books"
              :key="'b'+item.book_id"
              @click="selectEntity('book', item)"
            >
              <span>{{ item.title }}</span>
              <span class="item-extra">★ {{ item.score?.toFixed(1) || '?' }}</span>
            </div>
          </div>
          <!-- 作者 -->
          <div class="result-group" v-if="searchResults.authors?.length">
            <div class="group-title">✍️ 作者</div>
            <div
              class="result-item"
              v-for="item in searchResults.authors"
              :key="'a'+item.author_id"
              @click="selectEntity('author', item)"
            >
              <span>{{ item.name }}</span>
              <span class="item-extra" v-if="item.cnt">{{ item.cnt }} 本书</span>
            </div>
          </div>
          <!-- 出版社 -->
          <div class="result-group" v-if="searchResults.publishers?.length">
            <div class="group-title">🏢 出版社</div>
            <div
              class="result-item"
              v-for="item in searchResults.publishers"
              :key="'p'+item.publisher_id"
              @click="selectEntity('publisher', item)"
            >
              <span>{{ item.name }}</span>
              <span class="item-extra" v-if="item.cnt">{{ item.cnt }} 本书</span>
            </div>
          </div>
          <!-- 标签 -->
          <div class="result-group" v-if="searchResults.tags?.length">
            <div class="group-title">🏷️ 标签</div>
            <div
              class="result-item"
              v-for="item in searchResults.tags"
              :key="'t'+item.tag_id"
              @click="selectEntity('tag', item)"
            >
              <span>{{ item.name }}</span>
              <span class="item-extra" v-if="item.cnt">{{ item.cnt }} 本书</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 图谱统计（搜索栏右侧） -->
      <div class="graph-stats" v-if="!loading && !errorMsg">
        <span class="stat-item book">图书 {{ nodeCounts.book }}</span>
        <span class="stat-item author">作者 {{ nodeCounts.author }}</span>
        <span class="stat-item tag">标签 {{ nodeCounts.tag }}</span>
        <span class="stat-item publisher">出版社 {{ nodeCounts.publisher }}</span>
        <span class="stat-item link">关系 {{ linkCount }}</span>
      </div>

      <!-- 当前网络标题 & 操作 -->
      <div class="network-actions" v-if="currentEntity">
        <span class="current-label">
          当前：<strong>{{ currentEntity.type === 'book' ? '📕' : currentEntity.type === 'author' ? '✍️' : currentEntity.type === 'publisher' ? '🏢' : '🏷️' }}
          {{ currentEntity.name }}</strong>
        </span>
        <el-button size="small" @click="clearNetwork">清空</el-button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="graph-container" style="display:flex;align-items:center;justify-content:center;">
      <el-icon :size="40" class="is-loading"><Loading /></el-icon>
      <span style="margin-left:12px;color:#999;">加载图谱数据...</span>
    </div>

    <!-- Error -->
    <div v-else-if="errorMsg" class="graph-container" style="display:flex;align-items:center;justify-content:center;">
      <el-result icon="error" :title="errorMsg" sub-title="请检查网络连接或刷新重试">
        <template #extra>
          <el-button type="primary" @click="loadGraph">重新加载</el-button>
        </template>
      </el-result>
    </div>

    <!-- Graph -->
    <div
      v-else
      ref="chartRef"
      class="graph-container"
    ></div>

    <div class="legend" v-if="!loading && !errorMsg">
      <span v-for="cat in categories" :key="cat.name" class="legend-item">
        <span class="legend-dot" :style="{ background: cat.itemStyle.color }"></span>
        {{ cat.name }}
      </span>
      <span class="legend-hint">🖱️ 滚轮缩放 | 拖拽移动 | 悬停高亮 | 点击图书节点跳转管理</span>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { adminAPI } from '../../api/admin'
import * as echarts from 'echarts'

const router = useRouter()
const chartRef = ref(null)
const searchWrapRef = ref(null)
const loading = ref(true)
const errorMsg = ref('')

const searchKeyword = ref('')
const showDropdown = ref(false)
const searchResults = ref({ books: [], authors: [], publishers: [], tags: [] })
const hasResults = computed(() =>
  searchResults.value.books?.length > 0 ||
  searchResults.value.authors?.length > 0 ||
  searchResults.value.publishers?.length > 0 ||
  searchResults.value.tags?.length > 0
)

const currentEntity = ref(null)
const nodeCounts = reactive({ book: 0, author: 0, tag: 0, publisher: 0 })
const linkCount = ref(0)
const categories = ref([])

let chartInstance = null
let graphNodes = []
let graphLinks = []
let searchTimer = null

// ── 搜索 ──
async function onSearchFocus() {
  showDropdown.value = true
  if (searchKeyword.value && searchKeyword.value.trim()) return
  // 加载热门实体
  try {
    const res = await adminAPI.getGraphData({ popular: 1 })
    if (res.code === 200 && res.data.type === 'popular') {
      searchResults.value = {
        books: [],
        authors: (res.data.authors || []).map(a => ({ ...a, author_id: a.name })),
        publishers: (res.data.publishers || []).map(p => ({ ...p, publisher_id: p.name })),
        tags: (res.data.tags || []).map(t => ({ ...t, tag_id: t.name })),
      }
    }
  } catch { /* ignore */ }
}

async function onSearchInput() {
  const kw = searchKeyword.value.trim()
  if (!kw) {
    showDropdown.value = false
    return
  }
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    try {
      const res = await adminAPI.getGraphData({ keyword: kw })
      if (res.code === 200 && res.data.type === 'search_results') {
        searchResults.value = {
          books: res.data.books || [],
          authors: res.data.authors || [],
          publishers: res.data.publishers || [],
          tags: res.data.tags || [],
        }
        showDropdown.value = hasResults.value
      }
    } catch { /* ignore */ }
  }, 250)
}

function onSearchClear() {
  showDropdown.value = false
  searchResults.value = { books: [], authors: [], publishers: [], tags: [] }
}

// ── 实体选择 → 加载自我中心网络 ──
function selectEntity(type, item) {
  showDropdown.value = false
  searchKeyword.value = ''
  searchResults.value = { books: [], authors: [], publishers: [], tags: [] }

  currentEntity.value = { type, name: item.title || item.name }
  const params = {}
  if (type === 'book') params.book_id = item.book_id
  else if (type === 'author') params.author = item.name
  else if (type === 'publisher') params.publisher = item.name
  else if (type === 'tag') params.tag = item.name
  loadEgoNetwork(params)
}

// ── 加载自我中心网络 ──
async function loadEgoNetwork(params) {
  loading.value = true
  errorMsg.value = ''

  let res
  try {
    res = await adminAPI.getGraphData({ ...params, depth: 2 })
  } catch (e) {
    errorMsg.value = 'API 请求失败: ' + (e.message || '网络错误')
    loading.value = false
    return
  }

  if (res.code !== 200) {
    errorMsg.value = res.message || '数据获取失败'
    loading.value = false
    return
  }

  renderNetwork(res.data)
}

// ── 初始加载（空网络 + 统计） ──
async function loadGraph() {
  loading.value = true
  errorMsg.value = ''
  currentEntity.value = null

  let res
  try {
    res = await adminAPI.getGraphData()
  } catch (e) {
    errorMsg.value = 'API 请求失败: ' + (e.message || '网络错误')
    loading.value = false
    return
  }

  if (res.code !== 200) {
    errorMsg.value = res.message || '数据获取失败'
    loading.value = false
    return
  }

  const d = res.data
  categories.value = d.categories || []
  if (d.type === 'empty') {
    nodeCounts.book = d.nodes?.book || d.total_books || 0
    nodeCounts.author = d.nodes?.author || 0
    nodeCounts.tag = d.nodes?.tag || 0
    nodeCounts.publisher = d.nodes?.publisher || 0
    linkCount.value = 0
    errorMsg.value = '点击上方搜索框查找图书、作者、出版社或标签，即可展开知识图谱网络'
    loading.value = false
  } else if (d.type === 'top10_overview') {
    // 初始默认图谱
    nodeCounts.book = d.node_stats?.book || 0
    nodeCounts.author = d.node_stats?.author || 0
    nodeCounts.tag = d.node_stats?.tag || 0
    nodeCounts.publisher = d.node_stats?.publisher || 0
    renderNetwork(d)
  } else {
    renderNetwork(d)
  }
}

function clearNetwork() {
  currentEntity.value = null
  loadGraph()
}

// ── 图谱渲染 ──
function renderNetwork(d) {
  graphLinks = d.links || []
  categories.value = d.categories || []

  const engToCh = { book: '图书', author: '作者', tag: '标签', publisher: '出版社' }
  const chToIdx = {}
  ;(d.categories || []).forEach((c, i) => { chToIdx[c.name] = i })

  graphNodes = (d.nodes || []).map(n => ({
    ...n,
    category: chToIdx[engToCh[n.category]] ?? 0
  }))

  nodeCounts.book = graphNodes.filter(n => n.category === chToIdx['图书']).length
  nodeCounts.author = graphNodes.filter(n => n.category === chToIdx['作者']).length
  nodeCounts.tag = graphNodes.filter(n => n.category === chToIdx['标签']).length
  nodeCounts.publisher = graphNodes.filter(n => n.category === chToIdx['出版社']).length
  linkCount.value = graphLinks.length

  loading.value = false
  nextTick(() => {
    setTimeout(() => initChart(), 150)
  })
}

function initChart() {
  if (!chartRef.value) return
  const el = chartRef.value
  if (el.offsetWidth === 0 || el.offsetHeight === 0) {
    setTimeout(initChart, 200)
    return
  }

  if (chartInstance) { chartInstance.dispose(); chartInstance = null }

  try {
    chartInstance = echarts.init(el)

    const catNameToIdx = {}
    ;(categories.value || []).forEach((c, i) => { catNameToIdx[c.name] = i })

    chartInstance.setOption({
      tooltip: {
        formatter: (p) => {
          if (p.dataType === 'edge') return p.data.label || ''
          const catNames = categories.value.map(c => c.name)
          return `<b>${p.data.name}</b><br/>类型: ${catNames[p.data.category] || p.data.category}`
        },
      },
      animationDuration: 1000,
      series: [{
        type: 'graph',
        layout: 'force',
        force: { repulsion: 350, edgeLength: [80, 200], gravity: 0.06, friction: 0.6 },
        roam: true,
        draggable: true,
        data: graphNodes,
        links: graphLinks,
        categories: categories.value,
        label: {
          show: true, position: 'right', fontSize: 11, color: '#555',
          formatter: p => {
            const name = p.data.name || ''
            return name.length > 10 ? name.slice(0, 9) + '…' : name
          }
        },
        emphasis: { focus: 'adjacency', label: { fontSize: 14, fontWeight: 'bold' } },
        itemStyle: { borderColor: '#fff', borderWidth: 2 },
        lineStyle: { color: '#ccc', curveness: 0.2, opacity: 0.5 },
        edgeSymbol: ['none', 'none'],
        zoom: 1.2,
      }],
    })

    // 点击节点：图书节点跳转到管理页面并高亮
    chartInstance.on('click', (params) => {
      if (params.dataType === 'node') {
        const node = params.data
        if (node.category === catNameToIdx['图书']) {
          if (node.mysql_id) {
            router.push(`/admin/books?highlight=${node.mysql_id}&keyword=${encodeURIComponent(node.name || '')}`)
          }
        } else if (node.category === catNameToIdx['作者']) {
          // 点击作者节点 → 展开该作者网络
          currentEntity.value = { type: 'author', name: node.name }
          loadEgoNetwork({ author: node.name })
        } else if (node.category === catNameToIdx['标签']) {
          currentEntity.value = { type: 'tag', name: node.name }
          loadEgoNetwork({ tag: node.name })
        } else if (node.category === catNameToIdx['出版社']) {
          currentEntity.value = { type: 'publisher', name: node.name }
          loadEgoNetwork({ publisher: node.name })
        }
      }
    })
  } catch (e) {
    console.error('ECharts error:', e)
    errorMsg.value = '图表渲染失败'
  }
}

// 点击外部关闭下拉
function onClickOutside(e) {
  if (searchWrapRef.value && !searchWrapRef.value.contains(e.target)) {
    showDropdown.value = false
  }
}

let resizeHandler
onMounted(() => {
  loadGraph()
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
.kg-page { padding: 4px; }
.page-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; }
.page-header h2 { font-size: 20px; color: #2C3E50; margin: 0; }

.graph-stats {
  display: flex; align-items: center; gap: 10px; flex-shrink: 0;
  background: #fff; padding: 8px 16px; border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stat-item { padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 500; }
.stat-item.book { color: #D4A24C; background: #FFF8E7; }
.stat-item.author { color: #3498DB; background: #EEF5FB; }
.stat-item.tag { color: #2ECC71; background: #E8F8F0; }
.stat-item.publisher { color: #9B59B6; background: #F4ECF7; }
.stat-item.link { color: #95A5A6; background: #F5F5F5; }

/* 搜索栏 */
.search-row { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
.search-input-wrap { position: relative; flex: 1; min-width: 280px; max-width: 520px; }
.search-results {
  position: absolute; top: 100%; left: 0; right: 0; z-index: 2000;
  background: #fff; border: 1px solid #e0e0e0; border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12); max-height: 420px; overflow-y: auto;
  margin-top: 4px;
}
.result-group { padding: 4px 0; }
.result-group + .result-group { border-top: 1px solid #f0f0f0; }
.group-title { padding: 6px 14px; font-size: 12px; color: #999; font-weight: 600; }
.result-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 7px 14px; cursor: pointer; transition: background 0.15s;
}
.result-item:hover { background: #f5f7fa; }
.result-item span { font-size: 14px; color: #333; }
.item-extra { font-size: 12px; color: #aaa; }
.network-actions { display: flex; align-items: center; gap: 12px; }
.current-label { font-size: 13px; color: #666; }

/* 图谱容器 */
.graph-container {
  position: relative; overflow: hidden; background: #fff;
  border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  width: 100%; height: 70vh; min-height: 520px;
}
.legend { display: flex; align-items: center; gap: 16px; margin-top: 12px; font-size: 13px; color: #888; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 4px; }
.legend-dot { display: inline-block; width: 12px; height: 12px; border-radius: 50%; }
.legend-hint { margin-left: auto; font-size: 12px; color: #bbb; }
</style>
