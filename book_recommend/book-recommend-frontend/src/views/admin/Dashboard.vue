<template>
  <div class="overview">
    <div class="page-header">
      <div class="header-left">
        <h2>📊 数据总览</h2>
      </div>
    </div>

    <div class="stat-cards">
      <div class="stat-card" v-for="card in statCards" :key="card.label">
        <div class="card-icon" :style="{ background: card.color }">{{ card.icon }}</div>
        <div class="card-body">
          <div class="card-num">{{ card.value }}</div>
          <div class="card-label">{{ card.label }}</div>
          <div class="card-sub" v-if="card.sub">{{ card.sub }}</div>
        </div>
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-header">
          <h3>🏷️ 热门标签词云</h3>
          <span class="chart-hint">标签频次越高，字号越大</span>
        </div>
        <div ref="wordCloudRef" class="chart-box"></div>
      </div>
      <div class="chart-card">
        <div class="chart-header"><h3>💬 最新动态</h3></div>
        <div class="activity-list">
          <div class="activity-item" v-for="item in recentActivity" :key="item.id">
            <span class="activity-icon">{{ item.icon }}</span>
            <div class="activity-body">
              <p class="activity-text">{{ item.text }}</p>
              <span class="activity-time">{{ item.time }}</span>
            </div>
          </div>
          <div v-if="!recentActivity.length" style="color:#bbb;text-align:center;padding:20px">暂无动态</div>
        </div>
      </div>
    </div>

    <div class="charts-row charts-row--single">
      <div class="chart-card">
        <div class="chart-header">
          <h3>📈 用户活跃度</h3>
          <div class="chart-header-right">
            <button class="arrow-left-btn" @click="shiftTime(-1)" title="上一个周期">◀</button>
            <div class="mode-toggles">
              <button :class="['mode-btn', { active: activityMode === 'monthly' }]" @click="switchMode('monthly')">月</button>
              <button :class="['mode-btn', { active: activityMode === 'weekly' }]" @click="switchMode('weekly')">周</button>
              <button :class="['mode-btn', { active: activityMode === 'daily' }]" @click="switchMode('daily')">日</button>
            </div>
            <button class="arrow-right-btn" @click="shiftTime(1)" :disabled="timeOffset >= 0" title="下一个周期">▶</button>
            <span v-if="activity?.dateLabel" class="chart-date-label">{{ activity.dateLabel }}</span>
            <span class="chart-hint">峰值 {{ activityPeak }} · 均值 {{ activityAvg }}</span>
          </div>
        </div>
        <div ref="activityRef" class="chart-box chart-box--tall"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { adminAPI } from '../../api/admin'

const overview = ref(null)
const activity = ref(null)
const activityMode = ref('weekly')
const timeOffset = ref(0)  // 负数=向前翻，0=当前，正数=向后（仅未来，禁用）
const wordCloudRef = ref(null)
const activityRef = ref(null)
let chartInstance = null
let wordCloudInstance = null
let refreshTimer = null

const activityPeak = computed(() => activity.value?.peakLabel || '--')
const activityAvg = computed(() => activity.value?.avgCount || '--')

const COLORS = [
  '#d4a24c', '#2E4A3A', '#2980B9', '#8E44AD', '#E67E22', '#C0392B',
  '#16A085', '#2C3E50', '#3498DB', '#E74C3C', '#F39C12', '#1ABC9C',
  '#9B59B6', '#D35400', '#27AE60', '#e74c3c', '#f1c40f', '#00a8ff',
  '#9c88ff', '#273c75', '#c44569', '#3dc1d3', '#e66767', '#778beb',
  '#f5cd79', '#546de5', '#c3aed6', '#6a89cc', '#82ccdd', '#b8e994',
  '#f8a5c2', '#e77f67', '#3B3B98', '#58B19F', '#BDC581', '#EAB543',
]

function loadWordCloudScript() {
  return new Promise((resolve) => {
    if (window._wordCloudReady) return resolve()
    // MUST set global echarts BEFORE the script loads (it reads window.echarts)
    window.echarts = echarts
    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/echarts-wordcloud@2.1.0/dist/echarts-wordcloud.min.js'
    script.onload = () => { window._wordCloudReady = true; resolve() }
    script.onerror = () => { console.warn('Wordcloud CDN failed'); resolve() }
    document.head.appendChild(script)
  })
}

function renderWordCloud() {
  if (!wordCloudRef.value) return
  if (!overview.value?.tagCloud?.length) return
  if (wordCloudInstance) { wordCloudInstance.dispose(); wordCloudInstance = null }

  const chart = echarts.init(wordCloudRef.value)
  wordCloudInstance = chart

  // 预分配颜色：轮转分配确保相邻词不同色
  const shuffledColors = [...COLORS].sort(() => Math.random() - 0.5)
  const data = overview.value.tagCloud.map((d, i) => ({
    name: d.name,
    value: d.value,
    textStyle: { color: shuffledColors[i % shuffledColors.length] }
  }))

  chart.setOption({
    tooltip: { show: true, formatter: p => `${p.name}: ${p.value} 本书` },
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      keepAspect: false,
      width: '100%', height: '100%',
      left: 'center', top: 'center',
      sizeRange: [16, 60],
      rotationRange: [0, 0],
      rotationStep: 0,
      gridSize: 6,
      drawOutOfBound: false,
      layoutAnimation: true,
      textStyle: {
        fontFamily: '"Microsoft YaHei","PingFang SC",sans-serif',
        fontWeight: 'bold',
      },
      emphasis: {
        focus: 'self',
        textStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' }
      },
      data: data.sort(() => Math.random() - 0.5)
    }]
  })
}

const statCards = computed(() => {
  if (!overview.value) return []
  const b = overview.value.basic; const t = overview.value.trends
  return [
    { icon: '📚', label: '图书总量', value: b.books, color: '#d4a24c', sub: '' },
    { icon: '👤', label: '注册用户', value: b.users, color: '#2E4A3A', sub: '' },
    { icon: '✍️', label: '作者', value: b.authors, color: '#2980B9', sub: '' },
    { icon: '🏷️', label: '标签', value: b.tags, color: '#8E44AD', sub: '' },
    { icon: '💬', label: '评论', value: b.comments, color: '#E67E22', sub: '' },
  ]
})

const recentActivity = computed(() => {
  if (!overview.value) return []
  const items = []
  overview.value.recentComments?.forEach(c => items.push({
    id: `cmt-${c.id}`, icon: '💬',
    text: `${c.user} 评论了《${c.book}》：${c.content}`,
    rawTime: new Date(c.time).getTime(), time: formatTime(c.time)
  }))
  overview.value.recentUsers?.forEach(u => items.push({
    id: `usr-${u.id}`, icon: '👋',
    text: `${u.name} 注册成为新用户`,
    rawTime: new Date(u.time).getTime(), time: formatTime(u.time)
  }))
  return items.sort((a, b) => b.rawTime - a.rawTime).slice(0, 20)
})

function formatTime(t) {
  if (!t) return ''
  const diff = Date.now() - new Date(t).getTime()
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return new Date(t).toLocaleDateString('zh-CN')
}

function renderActivity() {
  if (!activityRef.value || !activity.value?.items?.length) return
  if (chartInstance) { chartInstance.dispose(); chartInstance = null }
  chartInstance = echarts.init(activityRef.value)
  const data = activity.value.items

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: p => {
        const item = data[p[0].dataIndex]
        return `<b>${item.label}</b><br/>活跃事件：<b>${item.total}</b> 次<br/>评论 ${item.comment} · 评分 ${item.rating}<br/>登录 ${item.login} · 阅读 ${item.reading}`
      }
    },
    grid: { left: 70, right: 25, top: 25, bottom: 40 },
    xAxis: {
      type: 'category', data: data.map(d => d.label),
      axisLabel: { fontSize: 11, rotate: activityMode.value === 'daily' ? 45 : 0 },
      boundaryGap: false,
    },
    yAxis: {
      type: 'value', name: '活动次数', nameLocation: 'end', nameGap: 10,
      nameTextStyle: { fontSize: 12 },
      minInterval: 1, axisLabel: { fontSize: 11 },
      splitLine: { lineStyle: { type: 'dashed', color: '#eee' } },
    },
    series: [{
      name: '活跃事件', type: 'line', smooth: true,
      symbol: 'circle', symbolSize: 5, data: data.map(d => d.total),
      lineStyle: { width: 3, color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#2980B9' }, { offset: 1, color: '#6BB9F0' }]) },
      itemStyle: { color: '#2980B9' },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(41,128,185,0.25)' }, { offset: 1, color: 'rgba(41,128,185,0.02)' }]) },
      markLine: {
        silent: true, symbol: 'none',
        data: [{ type: 'average', name: '均值', label: { formatter: '均值 {c}' } }],
        lineStyle: { color: '#E74C3C', type: 'dashed' },
      }
    }]
  })
}

async function switchMode(mode) {
  activityMode.value = mode
  timeOffset.value = 0
  const res = await adminAPI.getActivity(mode, timeOffset.value)
  if (res.code === 200) { activity.value = res.data; await nextTick(); renderActivity() }
}

async function shiftTime(dir) {
  timeOffset.value += dir
  if (timeOffset.value > 0) { timeOffset.value = 0; return }  // 不超出当前
  const res = await adminAPI.getActivity(activityMode.value, timeOffset.value)
  if (res.code === 200) { activity.value = res.data; await nextTick(); renderActivity() }
}

function handleResize() {
  if (chartInstance) { try { chartInstance.resize() } catch {} }
  if (wordCloudInstance) { try { wordCloudInstance.resize() } catch {} }
}

onMounted(async () => {
  const [resOv, resAct] = await Promise.all([adminAPI.getOverview(), adminAPI.getActivity('weekly', 0)])
  if (resOv.code === 200) { overview.value = resOv.data; await nextTick(); await loadWordCloudScript(); renderWordCloud() }
  if (resAct.code === 200) { activity.value = resAct.data; await nextTick(); renderActivity() }
  refreshTimer = setInterval(async () => {
    const r = await adminAPI.getOverview()
    if (r.code === 200) overview.value = r.data
  }, 30000)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  clearInterval(refreshTimer)
  window.removeEventListener('resize', handleResize)
  if (chartInstance) chartInstance.dispose()
  if (wordCloudInstance) wordCloudInstance.dispose()
})
</script>

<style scoped>
.overview { padding: 0 4px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.header-left h2 { font-size: 22px; color: #2C3E50; margin: 0; }
.header-sub { color: #999; font-size: 13px; margin: 4px 0 0; }

.stat-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 14px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: 12px; padding: 18px 20px; display: flex; align-items: center; gap: 16px; box-shadow: 0 1px 6px rgba(0,0,0,0.05); transition: transform 0.15s, box-shadow 0.15s; cursor: default; }
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.card-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; color: #fff; flex-shrink: 0; }
.card-num { font-size: 26px; font-weight: 700; color: #2C3E50; line-height: 1.1; }
.card-label { font-size: 13px; color: #888; margin-top: 2px; }
.card-sub { font-size: 11px; color: #16A085; margin-top: 2px; }

.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.charts-row--single { grid-template-columns: 1fr; }
.chart-card { background: #fff; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 6px rgba(0,0,0,0.05); }
.chart-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.chart-header h3 { font-size: 15px; color: #2C3E50; margin: 0; }
.chart-header-right { display: flex; align-items: center; gap: 12px; }
.chart-hint { font-size: 11px; color: #bbb; }
.chart-date-label { font-size: 13px; color: #d4a24c; font-weight: 600; }
.chart-box { width: 100%; height: 340px; }
.chart-box--tall { height: 380px; }

.mode-toggles { display: flex; gap: 0; border-radius: 6px; overflow: hidden; border: 1px solid #ddd; }
.mode-btn { padding: 4px 14px; font-size: 13px; border: none; background: #fff; color: #888; cursor: pointer; transition: all 0.15s; }
.mode-btn + .mode-btn { border-left: 1px solid #ddd; }
.mode-btn:hover { background: #f5f0eb; color: #2C3E50; }
.mode-btn.active { background: #d4a24c; color: #fff; }

.arrow-left-btn, .arrow-right-btn { padding: 3px 8px; border: 1px solid #ddd; background: #fafafa; border-radius: 4px; cursor: pointer; font-size: 12px; color: #888; transition: all 0.15s; }
.arrow-left-btn:hover, .arrow-right-btn:hover:not(:disabled) { border-color: #d4a24c; color: #d4a24c; background: #FFF8E7; }
.arrow-right-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.activity-list { display: flex; flex-direction: column; gap: 10px; height: 340px; overflow-y: auto; padding-right: 4px; }
.activity-item { display: flex; gap: 10px; padding: 8px 0; border-bottom: 1px solid #f5f5f5; }
.activity-icon { font-size: 18px; flex-shrink: 0; }
.activity-text { font-size: 13px; color: #444; margin: 0; line-height: 1.5; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 500px; }
.activity-time { font-size: 11px; color: #bbb; }

@media (max-width: 1200px) { .charts-row { grid-template-columns: 1fr; } }
@media (max-width: 768px) { .stat-cards { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); } }
</style>
