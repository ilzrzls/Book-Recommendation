<template>
  <div class="shelf-manager">
    <!-- Tab switcher -->
    <div class="shelf-tabs">
      <div class="tabs-group">
        <el-radio-group v-model="activeTab" size="large">
          <el-radio-button
            v-for="shelf in shelves"
            :key="shelf.id"
            :value="shelf.type"
          >
            {{ shelf.name }} ({{ shelf.items.length }})
            <el-dropdown
              v-if="activeTab === shelf.type"
              trigger="click"
              class="shelf-more"
              @command="(cmd) => handleShelfAction(cmd, shelf)"
            >
              <span class="more-trigger" @click.stop>
                <el-icon><MoreFilled /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">
                    <el-icon><Edit /></el-icon> 重命名
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-if="!['want_read','reading','read'].includes(shelf.type)"
                    command="delete"
                    divided
                  >
                    <el-icon><Delete /></el-icon> 删除书架
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </el-radio-button>
        </el-radio-group>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> 新建书架
      </el-button>
    </div>

    <!-- Book grid -->
    <div v-if="currentShelf && currentShelf.items.length > 0" class="shelf-grid">
      <div
        v-for="item in currentShelf.items"
        :key="item.id"
        class="shelf-book-wrapper"
      >
        <!-- Book Card + 按钮锚定区 -->
        <div class="book-card-anchor">
          <div @click="handleBookClick(item)" class="book-card-clickable">
            <BookCard :book="item.book" :progress="activeTab==='reading' ? item.reading_progress : 0" />
          </div>
          <el-dropdown
            trigger="click"
            class="book-action-dots"
            @command="(cmd) => handleBookAction(cmd, item)"
          >
            <el-button
              circle
              size="small"
              @click.stop
            >
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="detail">
                  <el-icon><View /></el-icon> 查看详情
                </el-dropdown-item>
                <el-dropdown-item v-if="isSystemShelf" command="move">
                  <el-icon><Switch /></el-icon> 移动
                </el-dropdown-item>
                <el-dropdown-item command="remove" divided>
                  <el-icon><Delete /></el-icon> 删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <!-- Reading progress bar at bottom (仅"在读"显示) -->
        <div class="book-progress-bar" v-if="activeTab==='reading' && item.reading_progress > 0 && item.reading_progress < 100">
          <div class="progress-fill" :style="{ width: item.reading_progress + '%' }"></div>
        </div>
        <div class="progress-text" v-if="activeTab==='reading' && item.reading_progress > 0 && item.reading_progress < 100">
          {{ item.reading_progress }}%
        </div>
      </div>
    </div>

    <el-empty
      v-if="!currentShelf || currentShelf.items.length === 0"
      description="书架空空的，快去发现好书吧~"
    />

    <!-- ============ Dialogs ============ -->

    <!-- Create / Edit shelf name -->
    <el-dialog
      v-model="shelfNameDialog.visible"
      :title="shelfNameDialog.isEdit ? '重命名书架' : '新建书架'"
      width="400px"
    >
      <el-input
        v-model="shelfNameDialog.name"
        placeholder="输入书架名称"
        maxlength="20"
        @keyup.enter="confirmShelfNameDialog"
      />
      <template #footer>
        <el-button @click="shelfNameDialog.visible = false">取消</el-button>
        <el-button
          type="primary"
          :disabled="!shelfNameDialog.name.trim()"
          @click="confirmShelfNameDialog"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- Delete shelf confirm -->
    <el-dialog
      v-model="deleteDialog.visible"
      title="删除书架"
      width="400px"
    >
      <p>确定要删除书架「{{ deleteDialog.name }}」吗？</p>
      <p class="hint-text">书架中的图书不会被删除，但会失去书架归属。</p>
      <template #footer>
        <el-button @click="deleteDialog.visible = false">取消</el-button>
        <el-button type="danger" @click="confirmDelete">删除</el-button>
      </template>
    </el-dialog>

    <!-- Edit reading progress -->
    <el-dialog v-model="progressDialog.visible" title="编辑阅读进度" width="420px">
      <div class="progress-dialog">
        <p class="book-name">{{ progressDialog.bookTitle }}</p>
        <!-- 页码输入 -->
        <div class="page-input-row" v-if="progressDialog.totalPages > 0">
          <span class="input-label">已读页码</span>
          <el-input-number
            v-model="progressDialog.currentPage"
            :min="0"
            :max="progressDialog.totalPages"
            :step="1"
            size="default"
            controls-position="right"
            @change="onPageChange"
          />
          <span class="input-suffix"> / {{ progressDialog.totalPages }} 页</span>
          <span class="auto-pct">{{ progressDialog.progress }}%</span>
        </div>
        <!-- 进度滑块 -->
        <el-slider v-model="progressDialog.progress" :max="100" show-input @change="onSliderChange" />
        <div class="progress-presets">
          <el-button size="small" @click="setProgress(0)">0%</el-button>
          <el-button size="small" @click="setProgress(25)">25%</el-button>
          <el-button size="small" @click="setProgress(50)">50%</el-button>
          <el-button size="small" @click="setProgress(75)">75%</el-button>
          <el-button size="small" @click="setProgress(100)">100%</el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="progressDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="confirmProgress">保存</el-button>
      </template>
    </el-dialog>

    <!-- Move book dialog -->
    <el-dialog v-model="moveDialog.visible" title="移动到书架" width="400px">
      <p class="book-name">{{ moveDialog.bookTitle }}</p>
      <el-radio-group v-model="moveDialog.targetType" class="move-options">
        <el-radio-button
          v-for="s in moveableShelves"
          :key="s.type"
          :value="s.type"
        >
          {{ s.name }} ({{ s.items.length }} 本)
        </el-radio-button>
      </el-radio-group>
      <template #footer>
        <el-button @click="moveDialog.visible = false">取消</el-button>
        <el-button type="primary" :disabled="!moveDialog.targetType" @click="confirmMove">移动</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { shelvesAPI } from '../../api/shelves'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../api/request'
import BookCard from '../common/BookCard.vue'

const router = useRouter()
const shelves = ref([])
const activeTab = ref('reading')

const systemShelves = ['want_read', 'reading', 'read']
const isSystemShelf = computed(() => systemShelves.includes(activeTab.value))

const currentShelf = computed(() => shelves.value.find(s => s.type === activeTab.value))
const moveableShelves = computed(() => shelves.value.filter(s => s.type !== activeTab.value))

// ---- Shelf name dialog (create / edit) ----
const shelfNameDialog = reactive({
  visible: false,
  isEdit: false,
  name: '',
  shelfId: null,
})

// ---- Delete shelf dialog ----
const deleteDialog = reactive({
  visible: false,
  name: '',
  shelfId: null,
})

// ---- Progress dialog ----
const progressDialog = reactive({
  visible: false,
  bookTitle: '',
  bookId: null,
  itemId: null,
  progress: 0,
  currentPage: 0,
  totalPages: 0,
})

function onPageChange(val) {
  if (progressDialog.totalPages > 0) {
    progressDialog.progress = Math.round((val / progressDialog.totalPages) * 100)
  }
}

function onSliderChange(val) {
  if (progressDialog.totalPages > 0) {
    progressDialog.currentPage = Math.round((val / 100) * progressDialog.totalPages)
  }
}

function setProgress(val) {
  progressDialog.progress = val
  if (progressDialog.totalPages > 0) {
    progressDialog.currentPage = Math.round((val / 100) * progressDialog.totalPages)
  }
}

// ---- Load shelves ----
onMounted(async () => {
  await loadShelves()
})

function goToBookDetail(item) {
  router.push(`/book/${item.book.id}`)
}
function handleBookClick(item) {
  if (!isSystemShelf.value) {
    router.push(`/read/${item.book.id}?page=0`)
  } else if (activeTab.value === 'reading' && item.reading_progress > 0) {
    const page = (item.current_page || 0) + 1
    router.push(`/read/${item.book.id}?page=${page}`)
  } else {
    router.push(`/book/${item.book.id}`)
  }
}
async function loadShelves() {
  const res = await shelvesAPI.getShelves()
  if (res.code === 200) {
    // 深拷贝确保 Vue 响应式检测到变化
    shelves.value = JSON.parse(JSON.stringify(res.data.shelves))
  }
}

// ============ Shelf actions ============
function openCreateDialog() {
  shelfNameDialog.visible = true
  shelfNameDialog.isEdit = false
  shelfNameDialog.name = ''
  shelfNameDialog.shelfId = null
}

function handleShelfAction(command, shelf) {
  if (command === 'edit') {
    shelfNameDialog.visible = true
    shelfNameDialog.isEdit = true
    shelfNameDialog.name = shelf.name
    shelfNameDialog.shelfId = shelf.id
  } else if (command === 'delete') {
    deleteDialog.visible = true
    deleteDialog.name = shelf.name
    deleteDialog.shelfId = shelf.id
  }
}

async function confirmShelfNameDialog() {
  const name = shelfNameDialog.name.trim()
  if (!name) return

  if (shelfNameDialog.isEdit) {
    const res = await shelvesAPI.updateShelf(shelfNameDialog.shelfId, name)
    if (res.code === 200) {
      ElMessage.success('书架已重命名')
      await loadShelves()
    } else {
      ElMessage.error(res.message)
    }
  } else {
    const res = await shelvesAPI.createShelf(name)
    if (res.code === 200) {
      ElMessage.success(`书架「${name}」创建成功`)
      await loadShelves()
      activeTab.value = res.data.type
    }
  }
  shelfNameDialog.visible = false
}

async function confirmDelete() {
  const res = await shelvesAPI.deleteShelf(deleteDialog.shelfId)
  if (res.code === 200) {
    ElMessage.success('书架已删除')
    activeTab.value = 'want_read'
    await loadShelves()
  } else {
    ElMessage.error(res.message)
  }
  deleteDialog.visible = false
}

// ============ Book actions ============

function handleBookAction(command, item) {
  if (command === 'detail') {
    router.push(`/book/${item.book.id}`)
  } else if (command === 'progress') {
    progressDialog.visible = true
    progressDialog.bookTitle = item.book.title
    progressDialog.bookId = item.book.id
    progressDialog.itemId = item.id
    progressDialog.progress = item.reading_progress
    progressDialog.totalPages = item.book?.total_pages || 0
    progressDialog.currentPage = item.current_page || 0
  } else if (command === 'move') {
    moveDialog.visible = true
    moveDialog.bookTitle = item.book.title
    moveDialog.itemId = item.id
    moveDialog.targetType = ''
  } else if (command === 'remove') {
    ElMessageBox.confirm(
      `确定要从「${currentShelf.value?.name}」中移除「${item.book.title}」吗？`,
      '移除图书',
      { confirmButtonText: '移除', cancelButtonText: '取消', type: 'warning' }
    ).then(async () => {
      const res = await shelvesAPI.removeItem(item.id)
      if (res.code === 200) {
        ElMessage.success(`「${item.book.title}」已移除`)
        await loadShelves()
      } else {
        ElMessage.error(res.message || '移除失败')
      }
    }).catch(() => {})
  }
}

// ---- Move dialog ----
const moveDialog = reactive({
  visible: false,
  bookTitle: '',
  itemId: null,
  targetType: '',
})

async function confirmMove() {
  if (!moveDialog.targetType) return
  const data = { shelf_type: moveDialog.targetType }
  // 移动到已读书架时，清除阅读进度
  if (moveDialog.targetType === 'read') {
    data.reading_progress = 0
  }
  const res = await shelvesAPI.updateItem(moveDialog.itemId, data)
  if (res.code === 200) {
    const targetShelf = shelves.value.find(s => s.type === moveDialog.targetType)
    ElMessage.success(`已移动到「${targetShelf?.name || moveDialog.targetType}」`)
    moveDialog.visible = false
    await loadShelves()
  } else {
    ElMessage.error(res.message || '移动失败')
  }
}

async function confirmProgress() {
  // 同步更新书架进度
  await shelvesAPI.updateItem(progressDialog.itemId, {
    reading_progress: progressDialog.progress,
  })
  // 同时写入 reading_progress 表（精确页码）
  try {
    await request.post('/user/progress', {
      book_id: progressDialog.bookId,
      current_page: progressDialog.currentPage,
      progress_pct: progressDialog.progress,
    })
  } catch { /* ignore */ }
  ElMessage.success('阅读进度已更新')
  progressDialog.visible = false
  await loadShelves()
}
</script>

<style scoped>
.shelf-manager {
  width: 100%;
}

.shelf-tabs {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.tabs-group {
  overflow-x: auto;
  max-width: 100%;
}

.shelf-more {
  margin-left: 4px;
  display: inline-flex;
  vertical-align: middle;
}

.more-trigger {
  cursor: pointer;
  padding: 2px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  transition: background 0.2s;
}
.more-trigger:hover {
  background: rgba(0,0,0,0.1);
}

.shelf-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
}

.shelf-book-wrapper {
  position: relative;
}

.book-action-dots {
  position: absolute;
  bottom: -12px;
  left: -12px;
  z-index: 10;
}
.book-action-dots :deep(.el-button) {
  background: rgba(255,255,255,0.92);
  box-shadow: 0 1px 4px rgba(0,0,0,0.12);
  border: 1px solid #eee;
}
.book-action-dots :deep(.el-button:hover) {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.book-progress-bar {
  height: 3px;
  background: #e8e8e8;
  border-radius: 0 0 12px 12px;
  overflow: hidden;
  margin-top: -1px;
}
.progress-text { font-size: 11px; color: #D4A24C; text-align: center; padding: 2px 0 4px; font-weight: 600; }
.book-card-anchor { position: relative; }
.book-card-clickable { cursor: pointer; }
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #D4A24C, #E67E22);
  border-radius: 0 0 12px 12px;
  transition: width 0.3s ease;
}

.hint-text {
  color: #999;
  font-size: 13px;
  margin-top: 8px;
}

.book-name {
  color: #2C3E50;
  font-weight: 600;
  margin-bottom: 16px;
  font-size: 15px;
}

.page-input-row {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 16px; padding: 10px 12px;
  background: #f8f9fa; border-radius: 8px;
}
.input-label { font-size: 13px; color: #666; flex-shrink: 0; }
.input-suffix { font-size: 13px; color: #999; flex-shrink: 0; }
.auto-pct { font-size: 20px; font-weight: bold; color: #D4A24C; margin-left: auto; }

.progress-dialog .el-slider {
  margin-bottom: 12px;
}

.progress-presets {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.move-options {
  display: flex;
  flex-direction: column;
  gap: 0;
  width: 100%;
}
.move-options :deep(.el-radio-button) {
  display: block;
  width: 100%;
}
.move-options :deep(.el-radio-button__inner) {
  display: block;
  width: 100%;
  text-align: left;
  padding: 10px 16px;
  border-radius: 8px !important;
  border: 1px solid #dcdfe6 !important;
  margin-bottom: 8px;
  transition: all 0.2s;
}
.move-options :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  border-color: #D4A24C !important;
  background: #FFF8E7;
  color: #2C3E50;
  box-shadow: none;
}

@media (max-width: 768px) {
  .shelf-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
  }
  .shelf-tabs {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
