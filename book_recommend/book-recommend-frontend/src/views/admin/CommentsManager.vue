<template>
  <div class="comments-manager">
    <div class="page-header">
      <h2>💬 评论管理</h2>
    </div>

    <div class="toolbar">
      <!-- 搜索框 + 防抖 -->
      <el-input v-model="searchKeyword" placeholder="搜索图书名称..."
        size="default" clearable @input="onSearchInput" @clear="search" style="width:220px">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <span class="toolbar-divider"></span>
      <!-- 三个互斥标签，点击即筛选 -->
      <span class="filter-tag" :class="{ active: selectedStatuses.includes('normal') }"
            @click="toggleStatus('normal')">正常</span>
      <span class="filter-tag" :class="{ active: selectedStatuses.includes('pinned') }"
            @click="toggleStatus('pinned')">已置顶</span>
      <span class="filter-tag deleted" :class="{ active: selectedStatuses.includes('deleted') }"
            @click="toggleStatus('deleted')">已删除</span>
      <span class="toolbar-hint" v-if="selectedStatuses.length === 0">（显示全部）</span>
    </div>

    <el-table :data="comments" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="65" />
      <el-table-column prop="book_title" label="图书" width="160" show-overflow-tooltip />
      <el-table-column prop="username" label="用户" width="100" />
      <el-table-column prop="content" label="内容" min-width="200" show-overflow-tooltip />
      <el-table-column prop="likes" label="点赞" width="60" />
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 'normal' ? 'success' : row.status === 'pinned' ? 'warning' : 'danger'" size="small">
            {{ { normal: '正常', pinned: '置顶', deleted: '已删' }[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="170" show-overflow-tooltip />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status !== 'deleted'">
            <el-button size="small" :type="row.status === 'pinned' ? 'warning' : 'info'"
              @click="togglePin(row)">
              {{ row.status === 'pinned' ? '取消' : '置顶' }}
            </el-button>
            <el-popconfirm title="确定删除该评论？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap">
      <el-pagination :current-page="page" :page-size="size" :total="total"
        layout="total, prev, pager, next" @current-change="(p) => { page = p; loadComments() }" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminAPI } from '../../api/admin'
import { ElMessage } from 'element-plus'

const comments = ref([])
const loading = ref(false)
const page = ref(1)
const size = ref(20)
const total = ref(0)
const searchKeyword = ref('')
let searchTimer = null

// 三个互斥标签
const selectedStatuses = ref([])

function toggleStatus(status) {
  if (selectedStatuses.value.includes(status)) {
    selectedStatuses.value = []     // 再次点击 → 取消选中 → 显示全部
  } else {
    selectedStatuses.value = [status]  // 单选互斥
  }
  search()
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => search(), 300)
}

async function loadComments() {
  loading.value = true
  const status = selectedStatuses.value.join(',')
  const res = await adminAPI.getComments(page.value, size.value, null, status, searchKeyword.value.trim())
  if (res.code === 200) {
    comments.value = res.data.items
    total.value = res.data.total
  }
  loading.value = false
}

function search() { page.value = 1; loadComments() }

async function togglePin(row) {
  const res = await adminAPI.pinComment(row.id, row.status !== 'pinned')
  if (res.code === 200) {
    ElMessage.success(row.status !== 'pinned' ? '已置顶' : '已取消置顶')
    loadComments()
  }
}

async function handleDelete(id) {
  const res = await adminAPI.deleteComment(id)
  if (res.code === 200) {
    ElMessage.success('评论已删除')
    loadComments()
  }
}

onMounted(loadComments)
</script>

<style scoped>
.page-header h2 { font-size: 20px; color: #2C3E50; margin: 0 0 16px 0; }
.toolbar { display: flex; gap: 10px; margin-bottom: 16px; align-items: center; flex-wrap: wrap; }
.toolbar-divider { width: 1px; height: 22px; background: #dcdfe6; display: inline-block; }

.filter-tag {
  padding: 4px 14px; border-radius: 16px; font-size: 13px;
  border: 1px solid #d9d9d9; background: #fafafa; cursor: pointer;
  transition: all 0.2s; user-select: none;
}
.filter-tag:hover { border-color: #D4A24C; color: #D4A24C; }
.filter-tag.active { background: #D4A24C; border-color: #D4A24C; color: #fff; }
.filter-tag.deleted.active { background: #e74c3c; border-color: #e74c3c; }

.toolbar-hint { font-size: 12px; color: #aaa; }

.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
