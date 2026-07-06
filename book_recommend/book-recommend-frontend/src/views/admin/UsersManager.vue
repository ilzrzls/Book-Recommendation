<template>
  <div class="users-manager">
    <div class="page-header">
      <h2>👤 用户管理</h2>
    </div>

    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索用户名..." style="width:240px" clearable @keyup.enter="search" @clear="search" />
      <span class="toolbar-divider"></span>
      <span class="filter-tag" :class="{ active: statusFilter === 'active' }"
            @click="toggleStatusFilter('active')">正常</span>
      <span class="filter-tag banned" :class="{ active: statusFilter === 'banned' }"
            @click="toggleStatusFilter('banned')">已禁用</span>
      <span class="toolbar-hint" v-if="!statusFilter">（显示全部）</span>
      <el-button @click="search" style="margin-left:auto">搜索</el-button>
    </div>

    <el-table :data="users" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="用户名" min-width="160" />
      <el-table-column prop="role" label="角色" width="90">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'warning' : 'info'" size="small">
            {{ row.role === 'admin' ? '管理员' : '读者' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
            {{ row.status === 'active' ? '正常' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="注册时间" min-width="170" show-overflow-tooltip />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <template v-if="row.role !== 'admin'">
            <el-popconfirm
              :title="row.status === 'active' ? '确定禁用该用户？' : '确定启用该用户？'"
              @confirm="toggleStatus(row)"
            >
              <template #reference>
                <el-button size="small" :type="row.status === 'active' ? 'danger' : 'success'">
                  {{ row.status === 'active' ? '禁用' : '启用' }}
                </el-button>
              </template>
            </el-popconfirm>
          </template>
          <span v-else class="hint">受保护</span>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap">
      <el-pagination :current-page="page" :page-size="size" :total="total"
        layout="total, prev, pager, next" @current-change="(p) => { page = p; loadUsers() }" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminAPI } from '../../api/admin'
import { ElMessage } from 'element-plus'

const users = ref([])
const loading = ref(false)
const page = ref(1)
const size = ref(20)
const total = ref(0)
const keyword = ref('')
const statusFilter = ref('')  // '' | 'active' | 'banned'

function toggleStatusFilter(status) {
  statusFilter.value = statusFilter.value === status ? '' : status
  search()
}

async function loadUsers() {
  loading.value = true
  const res = await adminAPI.getUsers(page.value, size.value, keyword.value, statusFilter.value)
  if (res.code === 200) {
    users.value = res.data.items
    total.value = res.data.total
  }
  loading.value = false
}

function search() { page.value = 1; loadUsers() }

async function toggleStatus(row) {
  const newStatus = row.status === 'active' ? 'banned' : 'active'
  const res = await adminAPI.updateUserStatus(row.id, newStatus)
  if (res.code === 200) {
    ElMessage.success(newStatus === 'active' ? '用户已启用' : '用户已禁用')
    loadUsers()
  }
}

onMounted(loadUsers)
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
.filter-tag.banned.active { background: #e74c3c; border-color: #e74c3c; }
.toolbar-hint { font-size: 12px; color: #aaa; }
.pagination-wrap { margin-top: 16px; display: flex; justify-content: flex-end; }
.hint { color: #999; font-size: 13px; }
</style>
