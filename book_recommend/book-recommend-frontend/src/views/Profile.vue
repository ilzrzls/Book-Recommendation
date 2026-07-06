<template>
  <div class="profile-page" v-loading="!profile">
    <div class="page-header">
      <h2>个人中心</h2>
    </div>

    <div class="profile-layout" v-if="profile">
      <!-- Sidebar -->
      <aside class="profile-sidebar">
        <div class="user-card">
          <div class="avatar-wrapper" @click="triggerUpload" title="点击更换头像">
            <el-avatar :size="80" :src="getAvatarUrl(profile.avatar, profile.username)" />
            <div class="avatar-overlay">
              <el-icon :size="20"><Camera /></el-icon>
            </div>
          </div>
          <input ref="fileInputRef" type="file" accept="image/jpeg,image/png,image/webp" style="display:none" @change="handleFileSelect" />
          <h3 class="username-row">
            {{ profile.username }}
            <el-icon class="edit-name-icon" :size="15" @click.stop="openEditName"><Edit /></el-icon>
          </h3>
        </div>
        <el-menu :default-active="activeMenu" @select="handleMenuSelect">
          <el-menu-item index="stats">
            <el-icon><DataAnalysis /></el-icon> 阅读统计
          </el-menu-item>
          <el-menu-item index="shelves">
            <el-icon><Collection /></el-icon> 我的创作
          </el-menu-item>
          <el-menu-item index="comments">
            <el-icon><ChatLineSquare /></el-icon> 评论历史
          </el-menu-item>
        </el-menu>
      </aside>

      <!-- Main Content -->
      <div class="profile-main">

        <!-- ====== Tab: 阅读统计 ====== -->
        <div v-if="activeMenu === 'stats'">
          <div class="stats-cards">
            <div class="stat-card">
              <el-icon :size="32" color="#3498DB"><Collection /></el-icon>
              <div class="stat-value">{{ stats.total_books }}<span class="unit"> 本</span></div>
              <div class="stat-label">书架藏书</div>
            </div>
            <div class="stat-card">
              <el-icon :size="32" color="#2E4A3A"><Check /></el-icon>
              <div class="stat-value">{{ stats.finished_books }}<span class="unit"> 本</span></div>
              <div class="stat-label">已读完</div>
            </div>
            <div class="stat-card">
              <el-icon :size="32" color="#D4A24C"><PriceTag /></el-icon>
              <div class="stat-value">{{ stats.tag_count }}<span class="unit"> 类</span></div>
              <div class="stat-label">偏好标签</div>
            </div>
          </div>
          <div class="chart-section" v-if="stats.tag_distribution && stats.tag_distribution.length">
            <h3>偏好标签分布</h3>
            <div ref="chartRef" class="chart-container"></div>
          </div>
          <el-empty v-else description="暂无阅读数据，去书架添加书籍开始阅读吧！" />

          <!-- ── 阅读时长统计 ── -->
          <h3 style="margin-top:24px">⏱ 阅读时长</h3>
          <div class="stats-cards reading-time-cards">
            <div class="stat-card time-card"><div class="stat-value">{{ formatDuration(readingTimeCards.today) }}</div><div class="stat-label">今日阅读</div></div>
            <div class="stat-card time-card"><div class="stat-value">{{ formatDuration(readingTimeCards.week) }}</div><div class="stat-label">本周阅读</div></div>
            <div class="stat-card time-card"><div class="stat-value">{{ formatDuration(readingTimeCards.month) }}</div><div class="stat-label">本月阅读</div></div>
            <div class="stat-card time-card"><div class="stat-value">{{ formatDuration(readingTimeCards.total) }}</div><div class="stat-label">累计阅读</div></div>
          </div>
          <!-- 每日折线图 -->
          <div v-if="readingTimeData && readingTimePeriod==='daily'" class="line-chart-wrap">
            <div ref="lineChartRef" class="line-chart-container"></div>
          </div>
          <!-- 周期切换 + 热力图（有数据才显示） -->
          <div v-if="readingTimeData" class="reading-time-section">
            <div class="period-switch">
              <el-radio-group v-model="readingTimePeriod" size="small" @change="loadReadingTimeData">
                <el-radio-button value="daily">每日</el-radio-button>
                <el-radio-button value="monthly">每月</el-radio-button>
              </el-radio-group>
            </div>
            <!-- 每日热力图 -->
            <div v-if="readingTimePeriod==='daily'" class="heatmap-grid-wrap">
              <div class="calendar-month-title">{{ readingTimeYear }}年{{ readingTimeMonth }}月</div>
              <div class="heatmap-body">
                <div class="heatmap-weekdays"><span v-for="d in weekDayLabels" :key="d">{{ d }}</span></div>
                <div class="calendar-grid">
                  <div v-for="(cell,idx) in calendarDays" :key="idx"
                    :class="['calendar-cell',{placeholder:!cell,'has-data':cell&&cell.total_seconds>0}]"
                    :style="cell&&cell.total_seconds>0?{background:getHeatColor(cell.total_seconds)}:{}"
                    @click="cell&&cell.total_seconds>0&&showDayDetail(cell.date)">
                    <span v-if="cell" class="calendar-day-num">{{ cell.day }}</span>
                  </div>
                </div>
              </div>
              <div class="heatmap-legend"><span>少</span><span v-for="l in 5" :key="l" class="legend-block" :style="{background:getHeatColor(l*600)}"></span><span>多</span></div>
            </div>
            <!-- 每月色块 -->
            <div v-else class="monthly-grid-wrap">
              <div class="calendar-month-title">{{ readingTimeYear }} 年</div>
              <div class="monthly-grid">
                <div v-for="m in yearlyMonths" :key="m.month"
                  :class="['monthly-cell',{'has-data':m.total_seconds>0}]"
                  :style="m.total_seconds>0?{background:getHeatColor(m.total_seconds)}:{}"
                  @click="m.total_seconds>0&&showPeriodDetail(m)">
                  <span class="monthly-label">{{ m.label }}</span>
                  <span class="monthly-time">{{ m.total_seconds>0?formatDuration(m.total_seconds):'' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 阅读详情弹窗 -->
        <Teleport to="body">
          <div v-if="readingDetailVisible" class="rd-modal-overlay" @click.self="readingDetailVisible=false">
            <div class="rd-modal reading-detail-modal">
              <h3>阅读详情 - {{ readingDetailDate }}</h3>
              <div class="detail-total">共阅读 {{ formatDuration(readingDetailTotalSec) }}</div>
              <div class="detail-book-list">
                <div v-for="b in readingDetailBooks" :key="b.book_id" class="detail-book-item" @click="router.push(`/book/${b.book_id}`);readingDetailVisible=false">
                  <el-image :src="getCoverUrl(b.cover)" class="detail-book-cover" fit="cover">
                    <template #error><div class="detail-cover-fallback"><el-icon :size="20"><Picture /></el-icon></div></template>
                  </el-image>
                  <div class="detail-book-info"><span class="detail-book-title">{{ b.title }}</span><span class="detail-book-time">{{ formatDuration(b.duration_seconds) }}</span></div>
                </div>
              </div>
            </div>
          </div>
        </Teleport>

        <!-- ====== Tab: 我的创作 ====== -->
        <div v-if="activeMenu === 'shelves'">
          <div class="shelf-tabs">
            <button
              v-for="s in creationShelves"
              :key="s.type"
              :class="['shelf-tab', { active: shelfTab === s.type }]"
              @click="shelfTab = s.type"
            >
              {{ s.name }} <span class="shelf-count">{{ s.count }}</span>
            </button>
            <button class="shelf-tab shelf-tab-add" @click="openNewShelfDialog">+ 新建书架</button>
          </div>

          <div v-if="creationShelves.length === 0" class="creation-empty">
            <el-empty description="还没有创作书架">
              <template #extra>
                <el-button type="primary" @click="openNewShelfDialog">新建书架</el-button>
                <el-button @click="router.push('/write')">去图图写作</el-button>
              </template>
            </el-empty>
          </div>

          <div v-else-if="currentCreationBooks.length" class="shelf-grid">
            <div
              v-for="item in currentCreationBooks"
              :key="item.id"
              class="shelf-book-card"
            >
              <div class="creation-card-cover" @click="router.push('/read/' + item.book.id + '?page=0')">
                <el-image :src="item.book.cover" fit="cover">
                  <template #error>
                    <div class="cover-fallback"><el-icon :size="32"><Picture /></el-icon></div>
                  </template>
                </el-image>
              </div>
              <div class="shelf-book-info" @click="router.push('/read/' + item.book.id + '?page=0')">
                <h4 class="shelf-book-title">{{ item.book.title }}</h4>
                <p class="shelf-book-author" v-if="item.book.author">{{ item.book.author }}</p>
              </div>
              <el-dropdown trigger="click" class="creation-card-menu" @command="(cmd) => handleCreationAction(cmd, item)">
                <el-button circle size="small" @click.stop>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="rename">
                      <el-icon><Edit /></el-icon> 重命名
                    </el-dropdown-item>
                    <el-dropdown-item command="cover">
                      <el-icon><Camera /></el-icon> 编辑封面
                    </el-dropdown-item>
                    <el-dropdown-item command="move">
                      <el-icon><Switch /></el-icon> 移动
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      <el-icon><Delete /></el-icon> 删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
          <el-empty v-else description="这个书架还是空的">
            <template #extra>
              <el-button type="primary" @click="router.push('/write')">去图图写作</el-button>
            </template>
          </el-empty>
        </div>

        <!-- 重命名作品弹窗 -->
        <el-dialog v-model="creationRenameDialog.visible" title="重命名作品" width="400px">
          <el-input v-model="creationRenameDialog.title" placeholder="输入新书名" maxlength="50" @keyup.enter="confirmCreationRename" />
          <template #footer>
            <el-button @click="creationRenameDialog.visible = false">取消</el-button>
            <el-button type="primary" :disabled="!creationRenameDialog.title.trim()" @click="confirmCreationRename">确定</el-button>
          </template>
        </el-dialog>

        <!-- 编辑封面弹窗 -->
        <el-dialog v-model="creationCoverDialog.visible" title="编辑封面" width="400px">
          <div class="cover-edit-row">
            <img v-if="creationCoverDialog.previewUrl" :src="creationCoverDialog.previewUrl" class="cover-edit-preview" />
            <div v-else class="cover-edit-empty" @click="triggerCreationCoverUpload">点击上传封面</div>
            <input ref="creationCoverInput" type="file" accept="image/jpeg,image/png,image/webp" style="display:none" @change="handleCreationCoverUpload" />
          </div>
          <template #footer>
            <el-button @click="creationCoverDialog.visible = false">取消</el-button>
            <el-button type="primary" @click="confirmCreationCover">保存</el-button>
          </template>
        </el-dialog>

        <!-- 移动作品弹窗 -->
        <el-dialog v-model="creationMoveDialog.visible" title="移动到书架" width="400px">
          <p>将《{{ creationMoveDialog.bookTitle }}》移动到：</p>
          <el-radio-group v-model="creationMoveDialog.targetType" class="move-options">
            <el-radio v-for="s in creationShelvesForMove" :key="s.type" :value="s.type">
              {{ s.name }} ({{ s.count }} 本)
            </el-radio>
          </el-radio-group>
          <template #footer>
            <el-button @click="creationMoveDialog.visible = false">取消</el-button>
            <el-button type="primary" :disabled="!creationMoveDialog.targetType" @click="confirmCreationMove">移动</el-button>
          </template>
        </el-dialog>

        <!-- 新建书架弹窗 -->
        <el-dialog v-model="creationNewShelfDialog.visible" title="新建书架" width="400px">
          <el-input v-model="creationNewShelfDialog.name" placeholder="输入书架名称" maxlength="20" @keyup.enter="confirmNewShelf" />
          <template #footer>
            <el-button @click="creationNewShelfDialog.visible = false">取消</el-button>
            <el-button type="primary" :disabled="!creationNewShelfDialog.name.trim()" @click="confirmNewShelf">确定</el-button>
          </template>
        </el-dialog>

        <!-- ====== Tab: 评论历史 ====== -->
        <div v-if="activeMenu === 'comments'">
          <div v-if="myComments.length" class="comment-list">
            <div
              v-for="c in myComments"
              :key="c.id"
              class="comment-history-item"
              @click="router.push(`/book/${c.book_id}`)"
            >
              <el-image :src="c.book_cover" class="comment-book-cover" fit="cover">
                <template #error><div class="cover-fallback-sm"><el-icon><Picture /></el-icon></div></template>
              </el-image>
              <div class="comment-body">
                <div class="comment-head">
                  <span class="comment-book-title">{{ c.book_title }}</span>
                  <span class="comment-date">{{ c.created_at }}</span>
                </div>
                <p class="comment-text">{{ c.content }}</p>
                <span class="comment-likes">
                  <el-icon><CaretTop /></el-icon> {{ c.likes }}
                </span>
              </div>
            </div>
          </div>
          <el-empty v-else description="还没有发表过评论，去图书详情页写下你的感悟吧！" />
        </div>

      </div>
    </div>

    <!-- ====== Crop Modal (Teleported) ====== -->
    <Teleport to="body">
      <div class="crop-overlay" v-if="cropVisible" @click.self="cancelCrop">
        <div class="crop-modal">
          <div class="crop-header">
            <h3>裁剪头像</h3>
            <button class="crop-close-btn" @click="cancelCrop">&times;</button>
          </div>
          <div class="crop-body">
            <div class="crop-frame" ref="cropWrapRef"
              @mousedown="startDrag" @touchstart.prevent="startDragTouch" @wheel.prevent="onWheel">
              <img ref="cropImgRef" :src="cropSrc" class="crop-img" @load="onCropImgLoad" draggable="false" />
              <div class="crop-circle-mask"></div>
              <svg class="crop-border-svg" viewBox="0 0 300 300">
                <circle cx="150" cy="150" r="149" fill="none" stroke="rgba(255,255,255,0.9)" stroke-width="2" />
              </svg>
            </div>
            <p class="crop-hint">滚动鼠标滚轮缩放 · 拖拽图片调整位置</p>
          </div>
          <div class="crop-footer">
            <button class="crop-btn crop-btn-cancel" @click="cancelCrop">取消</button>
            <button class="crop-btn crop-btn-confirm" :disabled="cropUploading" @click="confirmCrop">
              <span v-if="cropUploading" class="btn-spinner"></span>
              {{ cropUploading ? '上传中...' : '确认' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 修改昵称弹窗 -->
    <el-dialog v-model="editNameVisible" title="修改昵称" width="400px">
      <el-input v-model="editNameValue" placeholder="输入新昵称" maxlength="20" show-word-limit
        @keyup.enter="confirmEditName" />
      <template #footer>
        <el-button @click="editNameVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!editNameValue.trim()" :loading="editNameSaving" @click="confirmEditName">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { userAPI } from '../api/user'
import { shelvesAPI } from '../api/shelves'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../api/request'
import { getAvatarUrl } from '../utils/avatar'
import * as echarts from 'echarts'

const router = useRouter()
const userStore = useUserStore()
const profile = ref(null)
const activeMenu = ref('stats')
const chartRef = ref(null)
const fileInputRef = ref(null)
let chartInstance = null

// ---- Edit nickname ----
const editNameVisible = ref(false)
const editNameValue = ref('')
const editNameSaving = ref(false)
function openEditName() {
  editNameValue.value = profile.value?.username || ''
  editNameVisible.value = true
}
async function confirmEditName() {
  const name = editNameValue.value.trim()
  if (!name) return
  editNameSaving.value = true
  try {
    const res = await userStore.updateUsername(name)
    if (res.code === 200) {
      ElMessage.success('昵称修改成功')
      editNameVisible.value = false
    } else {
      ElMessage.error(res.message || '修改失败')
    }
  } catch { ElMessage.error('修改失败') }
  editNameSaving.value = false
}

// ---- Tab state ----
const shelves = ref([])
const shelfTab = ref('want_read')
const myComments = ref([])

const stats = computed(() => profile.value?.reading_stats || {
  total_books: 0,
  finished_books: 0,
  tag_count: 0,
  tag_distribution: [],
})

const creationShelves = computed(() => shelves.value)
const creationShelvesForMove = computed(() => creationShelves.value.filter(s => s.type !== shelfTab.value))
const currentCreationBooks = computed(() => {
  const s = creationShelves.value.find(x => x.type === shelfTab.value)
  return s?.items || []
})

// 创作管理弹窗
const creationRenameDialog = ref({ visible: false, bookId: null, title: '' })
const creationCoverDialog = ref({ visible: false, bookId: null, previewUrl: '' })
const creationNewCoverFile = ref(null)
const creationCoverInput = ref(null)
const creationMoveDialog = ref({ visible: false, bookId: null, bookTitle: '', itemId: null, targetType: '' })
const creationNewShelfDialog = ref({ visible: false, name: '' })

function handleCreationAction(cmd, item) {
  if (cmd === 'rename') {
    creationRenameDialog.value = { visible: true, bookId: item.book.id, title: item.book.title }
  } else if (cmd === 'cover') {
    creationCoverDialog.value = { visible: true, bookId: item.book.id, previewUrl: item.book.cover || '' }
    creationNewCoverFile.value = null
  } else if (cmd === 'move') {
    creationMoveDialog.value = { visible: true, bookId: item.book.id, bookTitle: item.book.title, itemId: item.id, targetType: '' }
  } else if (cmd === 'delete') {
    ElMessageBox.confirm(`确定要从书架中删除《${item.book.title}》吗？`, '删除作品', { type: 'warning', confirmButtonText: '删除' })
      .then(async () => {
        await shelvesAPI.removeItem(item.id)
        ElMessage.success('已删除')
        await loadShelves()
      }).catch(() => {})
  }
}

async function confirmCreationRename() {
  const title = creationRenameDialog.value.title.trim()
  if (!title) return
  try {
    await request.put('/tutuWrite/books/' + creationRenameDialog.value.bookId, { title })
    ElMessage.success('书名已更新')
    creationRenameDialog.value.visible = false
    await loadShelves()
  } catch { ElMessage.error('重命名失败') }
}

function triggerCreationCoverUpload() { creationCoverInput.value?.click() }

function handleCreationCoverUpload(e) {
  const file = e.target.files?.[0]
  if (!file) return
  creationNewCoverFile.value = file
  creationCoverDialog.value.previewUrl = URL.createObjectURL(file)
  e.target.value = ''
}

async function confirmCreationCover() {
  if (!creationNewCoverFile.value) { creationCoverDialog.value.visible = false; return }
  const fd = new FormData(); fd.append('file', creationNewCoverFile.value)
  try {
    const res = await request.post('/tutuWrite/upload-cover', fd)
    if (res.code === 200) {
      await request.put('/tutuWrite/books/' + creationCoverDialog.value.bookId, { cover_url: res.data.cover_url })
      ElMessage.success('封面已更新')
      creationCoverDialog.value.visible = false
      await loadShelves()
    }
  } catch { ElMessage.error('封面上传失败') }
}

async function confirmCreationMove() {
  if (!creationMoveDialog.value.targetType) return
  try {
    await shelvesAPI.updateItem(creationMoveDialog.value.itemId, { shelf_type: creationMoveDialog.value.targetType })
    ElMessage.success('已移动')
    creationMoveDialog.value.visible = false
    await loadShelves()
  } catch { ElMessage.error('移动失败') }
}

function openNewShelfDialog() {
  creationNewShelfDialog.value = { visible: true, name: '' }
}

async function confirmNewShelf() {
  const name = creationNewShelfDialog.value.name.trim()
  if (!name) return
  try {
    await request.post('/shelves', { name, shelf_type: 'writing' })
    ElMessage.success(`书架「${name}」已创建`)
    creationNewShelfDialog.value.visible = false
    await loadShelves()
    // 切换到新建的书架
    const created = shelves.value.find(s => s.name === name)
    if (created) shelfTab.value = created.type
  } catch { ElMessage.error('创建书架失败') }
}

// ---- Data loading ----
async function loadProfile() {
  await userStore.fetchProfile()
  profile.value = userStore.profile
  await nextTick()
  if (activeMenu.value === 'stats') renderChart()
}

async function loadShelves() {
  // 仅加载创作书架（type=writing），与主页书架独立
  const res = await request.get('/shelves', { params: { type: 'writing' } })
  if (res.code === 200) {
    shelves.value = res.data.shelves
    if (shelves.value.length > 0) {
      // 优先选中当前已选书架，否则选第一个
      const current = shelves.value.find(s => s.type === shelfTab.value)
      if (!current) shelfTab.value = shelves.value[0].type
    }
  }
}

async function loadComments() {
  const res = await userAPI.getComments()
  if (res.code === 200) {
    myComments.value = res.data.items
  }
}

// ── 阅读时长统计 ──
const readingTimePeriod = ref('daily')
const readingTimeYear = ref(new Date().getFullYear())
const readingTimeMonth = ref(new Date().getMonth()+1)
const readingTimeData = ref(null)
const readingTimeCards = ref({today:0,week:0,month:0,total:0})
const readingDetailVisible = ref(false)
const readingDetailDate = ref('')
const readingDetailBooks = ref([])
const readingDetailTotalSec = ref(0)
const lineChartRef = ref(null); let lineChartInstance = null
const weekDayLabels = ['一','二','三','四','五','六','日']

function formatDuration(seconds) {
  if (!seconds||seconds<60) return (seconds||0)+' 秒'
  if (seconds<3600) return Math.floor(seconds/60)+' 分钟'
  const h=Math.floor(seconds/3600), m=Math.floor((seconds%3600)/60)
  return h+' 小时'+ (m>0?m+' 分钟':'')
}
function getHeatColor(seconds) {
  const r=Math.min(1,seconds/3600)
  if(r<0.15) return '#c6e48b'; if(r<0.35) return '#7bc96f'; if(r<0.6) return '#239a3b'; return '#196127'
}
const calendarDays = computed(() => {
  if(!readingTimeData.value?.days) return []
  const y=readingTimeYear.value, m=readingTimeMonth.value
  const firstDay=new Date(y,m-1,1), totalDays=new Date(y,m,0).getDate()
  let startDow=firstDay.getDay(); startDow=startDow===0?6:startDow-1
  const result=[]
  for(let i=0;i<startDow;i++) result.push(null)
  const daysMap={}; (readingTimeData.value.days||[]).forEach(d=>{daysMap[d.date]=d.total_seconds})
  for(let d=1;d<=totalDays;d++){
    const dk=`${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`
    result.push({date:dk,day:d,total_seconds:daysMap[dk]||0})
  }
  return result
})
const yearlyMonths = computed(() => {
  if(!readingTimeData.value?.months) return []
  const y=readingTimeYear.value
  const map={};(readingTimeData.value.months||[]).forEach(m=>{map[m.month]=m.total_seconds})
  return ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'].map((label,i)=>{
    const key=`${y}-${String(i+1).padStart(2,'0')}`
    return {label,month:key,total_seconds:map[key]||0}
  })
})
async function loadReadingTimeData() {
  try{
    const res=await request.get('/user/reading-stats',{params:{period:readingTimePeriod.value,year:readingTimeYear.value,month:readingTimeMonth.value}})
    if(res.code===200){ readingTimeData.value=res.data; await nextTick(); renderLineChart() }
  }catch{}
}
function renderLineChart(){
  if(!lineChartRef.value||readingTimePeriod.value!=='daily') return
  if(lineChartInstance) lineChartInstance.dispose()
  lineChartInstance = echarts.init(lineChartRef.value)
  const days = readingTimeData.value?.days || []
  const totalDays = new Date(readingTimeYear.value, readingTimeMonth.value, 0).getDate()
  const dataMap = {}; days.forEach(d => { dataMap[d.date] = (d.total_seconds||0) / 60 })
  const xData = []; const yData = []
  for(let d=1; d<=totalDays; d++){
    const dk = `${readingTimeYear.value}-${String(readingTimeMonth.value).padStart(2,'0')}-${String(d).padStart(2,'0')}`
    xData.push(d+'日'); yData.push(Math.round(dataMap[dk]||0))
  }
  lineChartInstance.setOption({
    tooltip: { trigger: 'axis', formatter: p => `${p[0].axisValue}<br/>阅读 ${p[0].value} 分钟` },
    grid: { left: 40, right: 16, top: 16, bottom: 24 },
    xAxis: { type: 'category', data: xData, axisLabel: { fontSize: 10, color: '#999' }, axisTick: { show: false } },
    yAxis: { type: 'value', name: '分钟', min: 0, nameTextStyle: { fontSize: 10, color: '#999' }, axisLabel: { fontSize: 10, color: '#999' }, splitLine: { lineStyle: { color: '#f0ebe0' } } },
    series: [{ type: 'line', data: yData, smooth: true, symbol: 'circle', symbolSize: 4,
      lineStyle: { color: '#D4A24C', width: 2 },
      itemStyle: { color: '#D4A24C' },
      areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[
        { offset: 0, color: 'rgba(212,162,76,0.25)' }, { offset: 1, color: 'rgba(212,162,76,0.02)' }]) } }]
  })
}
async function loadReadingTimeCards() {
  try{
    const now=new Date(), y=now.getFullYear(), m=now.getMonth()+1
    const today=now.toISOString().slice(0,10)
    const [dr,wr,mr]=await Promise.all([
      request.get('/user/reading-stats/detail',{params:{date:today}}),
      request.get('/user/reading-stats',{params:{period:'daily',year:y,month:m}}),
      request.get('/user/reading-stats',{params:{period:'monthly',year:y}}),
    ])
    let weekSec=0, monthSec=0, totalSec=0
    if(wr.code===200){
      const days=wr.data.days||[]
      const weekStart=new Date(now); weekStart.setDate(now.getDate()-(now.getDay()||7)+1)
      const weekEnd=new Date(weekStart); weekEnd.setDate(weekStart.getDate()+6)
      days.forEach(d=>{const dt=new Date(d.date);if(dt>=weekStart&&dt<=weekEnd)weekSec+=d.total_seconds})
      days.forEach(d=>{monthSec+=d.total_seconds})
    }
    if(mr.code===200){(mr.data.months||[]).forEach(m=>{totalSec+=m.total_seconds})}
    readingTimeCards.value={today:dr.code===200?dr.data.total_seconds:0,week:weekSec,month:monthSec,total:totalSec}
  }catch{}
}
async function showDayDetail(date){
  readingDetailDate.value=date; readingDetailVisible.value=true
  try{const r=await request.get('/user/reading-stats/detail',{params:{date}});if(r.code===200){readingDetailBooks.value=r.data.books;readingDetailTotalSec.value=r.data.total_seconds}}catch{}
}
async function showPeriodDetail(m){
  readingDetailDate.value=m.label+' '+readingTimeYear.value; readingDetailVisible.value=true
  try{
    // 加载该月所有天，聚合每本书的时长
    const res=await request.get('/user/reading-stats',{params:{period:'daily',year:readingTimeYear.value,month:parseInt(m.month.split('-')[1])}})
    if(res.code===200){
      const bookMap={}; let total=0
      ;(res.data.days||[]).forEach(d=>{total+=d.total_seconds; Object.entries(d.books||{}).forEach(([bid,sec])=>{bookMap[bid]=(bookMap[bid]||0)+sec})})
      readingDetailTotalSec.value=total
      // 查书名
      const bids=Object.keys(bookMap)
      if(bids.length){
        try{
          const br=await request.get('/user/reading-stats/detail',{params:{date:res.data.days[0]?.date||''}})
          if(br.code===200){readingDetailBooks.value=br.data.books.map(b=>({...b,duration_seconds:bookMap[b.book_id]||b.duration_seconds}));return}
        }catch{}
      }
      readingDetailBooks.value=[]
    }
  }catch{}
}
function getCoverUrl(url){
  if(!url) return ''
  // 豆瓣图片通过后端代理加载
  if(url.includes('douban')||url.includes('img3')||url.includes('img9')) return '/api/v1/proxy/image?url='+encodeURIComponent(url)
  return url
}

function handleMenuSelect(index) {
  activeMenu.value = index
  if (index === 'stats') {
    nextTick(() => renderChart()); loadReadingTimeCards(); loadReadingTimeData()
  } else if (index === 'shelves') {
    loadShelves()
  } else if (index === 'comments') {
    loadComments()
  }
}

// ---- ECharts ----
function renderChart() {
  if (!chartRef.value) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartRef.value)
  const tags = stats.value.tag_distribution || []
  if (!tags.length) return
  const colors = ['#D4A24C','#3498DB','#2ECC71','#E67E22','#9B59B6','#1ABC9C','#E74C3C','#F39C12','#2980B9','#27AE60','#8E44AD','#16A085']
  const option = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} 本 ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 11 }, itemGap: 14, padding: [24, 0, 0, 0] },
    series: [{
      type: 'pie',
      radius: ['38%', '62%'],
      center: ['50%', '42%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}\n{d}%', fontSize: 10, distanceToLabelLine: 4 },
      emphasis: { label: { fontSize: 16, fontWeight: 'bold' } },
      data: tags.map((t, i) => ({ value: t.count, name: t.name, itemStyle: { color: colors[i % colors.length] } })),
    }],
  }
  chartInstance.setOption(option)
}

let resizeHandler = null

onMounted(async () => {
  await loadProfile()
  await loadShelves()
  loadReadingTimeCards(); loadReadingTimeData()
  resizeHandler = () => chartInstance?.resize()
  window.addEventListener('resize', resizeHandler)
})

onBeforeUnmount(() => {
  if (chartInstance) chartInstance.dispose()
  if (lineChartInstance) lineChartInstance.dispose()
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
  document.removeEventListener('mousemove', onGlobalMouseMove)
  document.removeEventListener('mouseup', onGlobalMouseUp)
  document.removeEventListener('touchmove', onGlobalTouchMove)
  document.removeEventListener('touchend', onGlobalTouchEnd)
})

watch(activeMenu, async (val) => {
  if (val === 'stats') { await nextTick(); renderChart() }
})

// ====================== Crop Logic (unchanged) ======================
const CROP_SIZE = 300
const OUTPUT_SIZE = 600
const MAX_FILE_SIZE = 5 * 1024 * 1024

const cropVisible = ref(false)
const cropSrc = ref('')
const cropImgRef = ref(null)
const cropWrapRef = ref(null)
const cropZoom = ref(1)
const cropUploading = ref(false)

let cropImgNatural = { w: 1, h: 1 }
let cropOffsetX = 0, cropOffsetY = 0
let dragging = false, dragStartX = 0, dragStartY = 0, dragStartOffX = 0, dragStartOffY = 0
let minZoom = 0.3, maxZoom = 4
let imageObjUrl = null, _rafPending = false

function updateCropImgStyle() {
  const img = cropImgRef.value
  if (!img) return
  img.style.width = (cropImgNatural.w * cropZoom.value) + 'px'
  img.style.height = (cropImgNatural.h * cropZoom.value) + 'px'
  img.style.transform = `translate(${cropOffsetX}px, ${cropOffsetY}px)`
}
function scheduleStyleUpdate() {
  if (!_rafPending) { _rafPending = true; requestAnimationFrame(() => { _rafPending = false; updateCropImgStyle() }) }
}
function onGlobalMouseMove(e) {
  if (!dragging) return
  let dx = e.clientX - dragStartX, dy = e.clientY - dragStartY
  let nx = dragStartOffX + dx, ny = dragStartOffY + dy
  const iw = cropImgNatural.w * cropZoom.value, ih = cropImgNatural.h * cropZoom.value
  const hw = (iw - CROP_SIZE) / 2, hy = (ih - CROP_SIZE) / 2
  const mx = Math.max(0, hw), my = Math.max(0, hy)
  if (nx > mx) { nx = mx + (nx - mx) * 0.35 } else if (nx < -mx) { nx = -mx + (nx + mx) * 0.35 }
  if (ny > my) { ny = my + (ny - my) * 0.35 } else if (ny < -my) { ny = -my + (ny + my) * 0.35 }
  cropOffsetX = nx; cropOffsetY = ny; scheduleStyleUpdate()
}
function onGlobalMouseUp() {
  if (!dragging) return; dragging = false; springBack()
}
function startDrag(e) {
  if (e.button !== 0) return
  dragging = true; dragStartX = e.clientX; dragStartY = e.clientY; dragStartOffX = cropOffsetX; dragStartOffY = cropOffsetY
  document.addEventListener('mousemove', onGlobalMouseMove); document.addEventListener('mouseup', onGlobalMouseUp)
}
function startDragTouch(e) {
  if (e.touches.length !== 1) return
  dragging = true; dragStartX = e.touches[0].clientX; dragStartY = e.touches[0].clientY; dragStartOffX = cropOffsetX; dragStartOffY = cropOffsetY
  document.addEventListener('touchmove', onGlobalTouchMove, { passive: false }); document.addEventListener('touchend', onGlobalTouchEnd)
}
function onGlobalTouchMove(e) {
  if (!dragging || e.touches.length !== 1) return; e.preventDefault()
  let dx = e.touches[0].clientX - dragStartX, dy = e.touches[0].clientY - dragStartY
  let nx = dragStartOffX + dx, ny = dragStartOffY + dy
  const iw = cropImgNatural.w * cropZoom.value, ih = cropImgNatural.h * cropZoom.value
  const hw = (iw - CROP_SIZE) / 2, hy = (ih - CROP_SIZE) / 2
  const mx = Math.max(0, hw), my = Math.max(0, hy)
  if (nx > mx) { nx = mx + (nx - mx) * 0.35 } else if (nx < -mx) { nx = -mx + (nx + mx) * 0.35 }
  if (ny > my) { ny = my + (ny - my) * 0.35 } else if (ny < -my) { ny = -my + (ny + my) * 0.35 }
  cropOffsetX = nx; cropOffsetY = ny; scheduleStyleUpdate()
}
function onGlobalTouchEnd() {
  if (!dragging) return; dragging = false; springBack()
  document.removeEventListener('touchmove', onGlobalTouchMove); document.removeEventListener('touchend', onGlobalTouchEnd)
}
function springBack() {
  const iw = cropImgNatural.w * cropZoom.value, ih = cropImgNatural.h * cropZoom.value
  const hw = (iw - CROP_SIZE) / 2, hyA = (ih - CROP_SIZE) / 2
  let tx = cropOffsetX, ty = cropOffsetY
  const mx = Math.max(0, hw), my = Math.max(0, hyA)
  if (tx > mx) tx = mx; else if (tx < -mx) tx = -mx
  if (ty > my) ty = my; else if (ty < -my) ty = -my
  if (tx === cropOffsetX && ty === cropOffsetY) return
  const sx = cropOffsetX, sy = cropOffsetY, st = performance.now()
  function anim(now) {
    const t = Math.min((now - st) / 200, 1), e = 1 - Math.pow(1 - t, 3)
    cropOffsetX = sx + (tx - sx) * e; cropOffsetY = sy + (ty - sy) * e; updateCropImgStyle()
    if (t < 1) requestAnimationFrame(anim)
  }
  requestAnimationFrame(anim)
}
function onWheel(e) {
  const oz = cropZoom.value, factor = e.deltaY > 0 ? 0.9 : 1.1
  let nz = oz * factor; if (nz < minZoom) nz = minZoom; if (nz > maxZoom) nz = maxZoom
  if (nz === oz) return
  const cx = CROP_SIZE / 2, cy = CROP_SIZE / 2, icx = cx - cropOffsetX, icy = cy - cropOffsetY, s = nz / oz
  cropOffsetX = cx - icx * s; cropOffsetY = cy - icy * s; cropZoom.value = nz; updateCropImgStyle()
}
function triggerUpload() { fileInputRef.value?.click() }
function handleFileSelect(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (!['image/jpeg','image/png','image/webp'].includes(file.type)) { ElMessage.error('仅支持 JPG、PNG、WebP'); e.target.value = ''; return }
  if (file.size > MAX_FILE_SIZE) { ElMessage.error('图片不能超过 5MB'); e.target.value = ''; return }
  if (imageObjUrl) URL.revokeObjectURL(imageObjUrl)
  imageObjUrl = URL.createObjectURL(file); cropSrc.value = imageObjUrl; cropZoom.value = 1; cropOffsetX = 0; cropOffsetY = 0; cropUploading.value = false; cropVisible.value = true
  document.body.style.overflow = 'hidden'; e.target.value = ''
}
function onCropImgLoad() {
  const img = cropImgRef.value; if (!img) return
  cropImgNatural = { w: img.naturalWidth, h: img.naturalHeight }
  const sw = CROP_SIZE / cropImgNatural.w, sh = CROP_SIZE / cropImgNatural.h, iz = Math.max(sw, sh)
  cropZoom.value = iz; minZoom = Math.min(sw, sh) * 0.5; if (minZoom < 0.1) minZoom = 0.1; maxZoom = Math.max(iz * 3, 3)
  const w = cropImgNatural.w * iz, h = cropImgNatural.h * iz; cropOffsetX = (CROP_SIZE - w) / 2; cropOffsetY = (CROP_SIZE - h) / 2; updateCropImgStyle()
}
async function confirmCrop() {
  const img = cropImgRef.value; if (!img) return; cropUploading.value = true
  const canvas = document.createElement('canvas'); canvas.width = OUTPUT_SIZE; canvas.height = OUTPUT_SIZE; const ctx = canvas.getContext('2d')
  const dw = cropImgNatural.w * cropZoom.value, dh = cropImgNatural.h * cropZoom.value, sx = cropImgNatural.w / dw, sy = cropImgNatural.h / dh
  const scx = (CROP_SIZE / 2 - cropOffsetX) * sx, scy = (CROP_SIZE / 2 - cropOffsetY) * sy, sr = (CROP_SIZE / 2) * sx
  ctx.beginPath(); ctx.arc(OUTPUT_SIZE / 2, OUTPUT_SIZE / 2, OUTPUT_SIZE / 2, 0, Math.PI * 2); ctx.clip()
  ctx.drawImage(img, scx - sr, scy - sr, sr * 2, sr * 2, 0, 0, OUTPUT_SIZE, OUTPUT_SIZE)
  const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg', 0.92)); const fd = new FormData(); fd.append('file', blob, 'avatar.jpg')
  try {
    const res = await request.post('/auth/avatar', fd)
    if (res.code === 200) {
      const na = res.data.avatar_url + '?t=' + Date.now(); profile.value.avatar = na
      userStore.updateAvatar(na)
      ElMessage.success('头像已更新！'); closeCrop()
    } else { ElMessage.error(res.message || '上传失败') }
  } catch { ElMessage.error('头像上传失败') }
  cropUploading.value = false
}
function cancelCrop() { closeCrop() }
function closeCrop() {
  cropVisible.value = false; cropSrc.value = ''; document.body.style.overflow = ''
  if (imageObjUrl) { URL.revokeObjectURL(imageObjUrl); imageObjUrl = null }
  document.removeEventListener('mousemove', onGlobalMouseMove); document.removeEventListener('mouseup', onGlobalMouseUp)
  document.removeEventListener('touchmove', onGlobalTouchMove); document.removeEventListener('touchend', onGlobalTouchEnd)
}
</script>

<style scoped>
.profile-page { max-width: 1200px; margin: 0 auto; padding: 20px; }
.page-header h2 { font-size: 24px; color: #2C3E50; margin-bottom: 20px; }
.profile-layout { display: flex; gap: 24px; }
.profile-sidebar { width: 220px; flex-shrink: 0; }
.user-card { background: #fff; border-radius: 12px; padding: 24px; text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 16px; }
.avatar-wrapper { position: relative; display: inline-block; cursor: pointer; border-radius: 50%; overflow: hidden; }
.avatar-wrapper .avatar-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.4); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; opacity: 0; transition: opacity 0.2s; }
.avatar-wrapper:hover .avatar-overlay { opacity: 1; }
.username-row { margin-top: 12px; color: #2C3E50; font-size: 18px; display: flex; align-items: center; justify-content: center; gap: 6px; }
.edit-name-icon { cursor: pointer; color: #bbb; transition: color 0.2s; }
.edit-name-icon:hover { color: #D4A24C; }
.profile-main { flex: 1; min-width: 0; }

/* Stats */
.stats-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
.stat-card { background: #fff; border-radius: 12px; padding: 24px; text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
.stat-value { font-size: 28px; font-weight: bold; color: #2C3E50; margin: 8px 0 4px; }
.stat-value .unit { font-size: 14px; font-weight: normal; color: #999; }
.stat-label { font-size: 13px; color: #888; }
.chart-section { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
.chart-section h3 { color: #2C3E50; margin-bottom: 16px; font-size: 16px; }
.chart-container { width: 100%; height: 400px; margin-bottom: 24px; }

/* Shelves */
.shelf-tabs { display: flex; gap: 0; margin-bottom: 20px; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.shelf-tab { flex: 1; padding: 12px 0; text-align: center; border: none; background: transparent; font-size: 14px; color: #666; cursor: pointer; transition: all 0.2s; border-bottom: 3px solid transparent; }
.shelf-tab:hover { color: #D4A24C; background: #FFFDF5; }
.shelf-tab.active { color: #D4A24C; border-bottom-color: #D4A24C; font-weight: 600; }
.shelf-count { margin-left: 4px; font-size: 12px; color: #aaa; }
.shelf-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.shelf-book-card { display: flex; gap: 12px; background: #fff; border-radius: 10px; padding: 12px; cursor: pointer; transition: box-shadow 0.2s; box-shadow: 0 1px 6px rgba(0,0,0,0.06); }
.shelf-book-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.shelf-book-cover { width: 60px; height: 84px; border-radius: 6px; flex-shrink: 0; }
.cover-fallback { width: 60px; height: 84px; background: #f0ede8; display: flex; align-items: center; justify-content: center; color: #ccc; border-radius: 6px; }
.shelf-book-info { flex: 1; min-width: 0; display: flex; flex-direction: column; justify-content: center; gap: 4px; }
.shelf-book-title { font-size: 15px; color: #2C3E50; margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.shelf-book-author { font-size: 12px; color: #999; margin: 0; }
.shelf-progress-text { font-size: 11px; color: #D4A24C; }
.shelf-tab-add { flex: 0 0 auto; padding: 12px 18px; color: #D4A24C; font-weight: 600; border-left: 1px solid #eee; white-space: nowrap; }
.shelf-tab-add:hover { background: #FFF8E1; }
.creation-empty { padding: 40px 0; }
.creation-card-cover { width: 60px; height: 84px; border-radius: 6px; flex-shrink: 0; overflow: hidden; cursor: pointer; }
.creation-card-cover .el-image { width: 100%; height: 100%; }
.creation-card-menu { flex-shrink: 0; align-self: center; }
.cover-edit-row { text-align: center; }
.cover-edit-preview { max-width: 200px; max-height: 280px; border-radius: 8px; cursor: pointer; }
.cover-edit-empty { width: 200px; height: 280px; border: 2px dashed #ddd; border-radius: 8px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #999; font-size: 14px; }
.cover-edit-empty:hover { border-color: #D4A24C; color: #D4A24C; }
.move-options { display: flex; flex-direction: column; gap: 8px; padding: 12px 0; }
.move-options .el-radio { margin-right: 0; }

/* Comments */
.comment-list { display: flex; flex-direction: column; gap: 12px; }
.comment-history-item { display: flex; gap: 12px; background: #fff; border-radius: 10px; padding: 14px; cursor: pointer; transition: box-shadow 0.2s; box-shadow: 0 1px 6px rgba(0,0,0,0.06); }
.comment-history-item:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.comment-book-cover { width: 48px; height: 64px; border-radius: 4px; flex-shrink: 0; }
.cover-fallback-sm { width: 48px; height: 64px; background: #f0ede8; display: flex; align-items: center; justify-content: center; color: #ccc; border-radius: 4px; }
.comment-body { flex: 1; min-width: 0; }
.comment-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; }
.comment-book-title { font-size: 14px; font-weight: 600; color: #D4A24C; }
.comment-date { font-size: 12px; color: #bbb; }
.comment-text { font-size: 13px; color: #555; line-height: 1.5; margin: 0 0 6px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.comment-likes { font-size: 12px; color: #999; display: flex; align-items: center; gap: 2px; }

/* Placeholder area */
.placeholder-section { padding: 60px 0; }

.reading-time-cards .time-card .stat-value{font-size:20px;font-weight:700}
.line-chart-wrap{margin-top:16px}
.line-chart-container{width:100%;height:180px}
.period-switch{margin:16px 0 12px}
.heatmap-grid-wrap,.monthly-grid-wrap{margin-top:8px}
.calendar-month-title{font-size:14px;font-weight:600;color:#2C3E50;margin-bottom:10px}
.heatmap-body{display:flex;flex-direction:column;gap:4px;width:100%}
.heatmap-weekdays{display:grid;grid-template-columns:repeat(7,1fr);gap:3px;padding:0}
.heatmap-weekdays span{font-size:11px;color:#999;height:20px;line-height:20px;text-align:center}
.calendar-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:3px}
.calendar-cell{border-radius:4px;background:#f0ebe0;display:flex;align-items:center;justify-content:center;cursor:default;font-size:11px;color:#bbb;transition:transform .15s;height:22px}
.calendar-cell.placeholder{background:transparent}
.calendar-cell.has-data{cursor:pointer;color:#fff;font-weight:600}
.calendar-cell.has-data:hover{transform:scale(1.2);z-index:1}
.heatmap-legend{display:flex;align-items:center;gap:4px;margin-top:8px;font-size:11px;color:#999}
.legend-block{width:16px;height:12px;border-radius:2px}
.monthly-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.monthly-cell{border-radius:10px;padding:16px 12px;background:#f0ebe0;text-align:center;cursor:default;transition:transform .15s}
.monthly-cell.has-data{cursor:pointer;color:#fff}
.monthly-cell.has-data:hover{transform:scale(1.05)}
.monthly-label{display:block;font-size:13px;font-weight:600;color:#555}
.monthly-time{display:block;font-size:11px;color:#888;margin-top:4px}
.monthly-cell.has-data .monthly-label,.monthly-cell.has-data .monthly-time{color:#fff}
.reading-detail-modal{width:420px;max-width:95vw;padding:24px;background:#fff;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,0.2)}
.reading-detail-modal h3{font-size:16px;color:#2C3E50;margin:0 0 12px}
.detail-total{font-size:13px;color:#999;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #f0ebe0}
.detail-book-item{display:flex;align-items:center;gap:12px;padding:10px 8px;cursor:pointer;border-radius:8px;transition:background .15s}
.detail-book-item:hover{background:#f8f4ec}
.detail-book-cover{width:40px;height:56px;border-radius:4px;flex-shrink:0}
.detail-cover-fallback{width:40px;height:56px;border-radius:4px;background:#f0ebe0;display:flex;align-items:center;justify-content:center;color:#ccc}
.detail-book-info{flex:1;display:flex;flex-direction:column;gap:2px}
.detail-book-title{font-size:13px;color:#2C3E50;font-weight:500}
.detail-book-time{font-size:11px;color:#999}
.rd-modal-overlay{position:fixed;inset:0;z-index:11000;background:rgba(26,54,80,0.45);backdrop-filter:blur(4px);display:flex;align-items:center;justify-content:center}
@media (max-width: 768px) {
  .profile-layout { flex-direction: column; }
  .profile-sidebar { width: 100%; }
  .shelf-grid { grid-template-columns: 1fr; }
  .calendar-grid{grid-template-columns:repeat(7,1fr)}
  .calendar-cell{font-size:10px}
  .heatmap-weekdays{grid-template-columns:repeat(7,1fr)}
}
</style>

<!-- Crop modal unscoped (Teleported) -->
<style>
.crop-overlay { position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,0.45); backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; animation: crop-overlay-in 0.2s ease; }
@keyframes crop-overlay-in { from { opacity: 0; } to { opacity: 1; } }
.crop-modal { background: #1e1e1e; border-radius: 16px; width: 420px; max-width: 95vw; box-shadow: 0 24px 80px rgba(0,0,0,0.5); display: flex; flex-direction: column; overflow: hidden; animation: crop-modal-in 0.25s cubic-bezier(0.22,0.61,0.36,1); }
@keyframes crop-modal-in { from { transform: scale(0.92); opacity: 0; } to { transform: scale(1); opacity: 1; } }
.crop-header { display: flex; align-items: center; justify-content: space-between; padding: 18px 24px 12px; }
.crop-header h3 { color: #fff; font-size: 17px; font-weight: 600; margin: 0; }
.crop-close-btn { background: none; border: none; color: #888; font-size: 24px; cursor: pointer; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 50%; transition: all 0.15s; line-height: 1; }
.crop-close-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }
.crop-body { display: flex; flex-direction: column; align-items: center; padding: 8px 24px 16px; }
.crop-frame { width: 300px; height: 300px; position: relative; cursor: move; user-select: none; touch-action: none; overflow: hidden; border-radius: 50%; background: #111; }
.crop-img { position: absolute; left: 0; top: 0; pointer-events: none; will-change: transform; }
.crop-circle-mask { position: absolute; inset: 0; border-radius: 50%; box-shadow: 0 0 0 9999px rgba(0,0,0,0.55); pointer-events: none; }
.crop-border-svg { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
.crop-hint { margin: 14px 0 0; font-size: 13px; color: #777; text-align: center; }
.crop-footer { display: flex; gap: 12px; padding: 12px 24px 20px; justify-content: flex-end; }
.crop-btn { padding: 10px 28px; border-radius: 8px; font-size: 15px; font-weight: 500; border: none; cursor: pointer; transition: all 0.15s; }
.crop-btn-cancel { background: rgba(255,255,255,0.08); color: #ccc; }
.crop-btn-cancel:hover { background: rgba(255,255,255,0.15); color: #fff; }
.crop-btn-confirm { background: #D4A24C; color: #fff; min-width: 90px; display: inline-flex; align-items: center; justify-content: center; gap: 8px; }
.crop-btn-confirm:hover:not(:disabled) { background: #c8943c; }
.crop-btn-confirm:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: crop-spin 0.6s linear infinite; }
@keyframes crop-spin { to { transform: rotate(360deg); } }
</style>
