<template>
  <div class="admin-layout">
    <!-- Sidebar -->
    <aside class="admin-sidebar">
      <div class="sidebar-header">
        <h2>⚙️ 管理后台</h2>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/admin" exact-active-class="active" class="nav-item">
          <el-icon><DataAnalysis /></el-icon> 数据总览
        </router-link>
        <router-link to="/admin/books" active-class="active" class="nav-item">
          <el-icon><Reading /></el-icon> 图书管理
        </router-link>
        <router-link to="/admin/users" active-class="active" class="nav-item">
          <el-icon><User /></el-icon> 用户管理
        </router-link>
        <router-link to="/admin/comments" active-class="active" class="nav-item">
          <el-icon><ChatDotRound /></el-icon> 评论管理
        </router-link>
        <router-link to="/admin/graph" active-class="active" class="nav-item">
          <el-icon><Link /></el-icon> 知识图谱
        </router-link>
        <div class="nav-divider"></div>
        <router-link to="/" class="nav-item">
          <el-icon><HomeFilled /></el-icon> 返回前台
        </router-link>
      </nav>
    </aside>

    <!-- Main Content -->
    <main class="admin-main">
      <router-view />
    </main>

    <!-- 浮动头像（右上角，点击弹出菜单） -->
    <div class="floating-avatar">
      <el-dropdown trigger="click" placement="bottom-end">
        <span class="avatar-trigger">
          <el-avatar :size="34" :src="avatarUrl" />
          <span class="avatar-name">{{ adminName }}</span>
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="triggerUpload">
              <el-icon><Camera /></el-icon> 更换头像
            </el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">
              <el-icon><SwitchButton /></el-icon> 退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <input ref="fileInput" type="file" accept="image/jpeg,image/png,image/webp" style="display:none" @change="handleUpload" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../../api/request'

const router = useRouter()
const fileInput = ref(null)
const adminName = ref('')
const adminAvatar = ref('')
const avatarUrl = computed(() => adminAvatar.value || '')

onMounted(async () => {
  try {
    const res = await request.get('/auth/profile')
    if (res.code === 200) {
      adminName.value = res.data.username || '管理员'
      adminAvatar.value = res.data.avatar || ''
    }
  } catch {}
})

function triggerUpload() { fileInput.value?.click() }

async function handleUpload(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) { ElMessage.error('图片不能超过 5MB'); return }
  const fd = new FormData(); fd.append('file', file)
  try {
    const res = await request.post('/auth/avatar', fd)
    if (res.code === 200) {
      adminAvatar.value = res.data.avatar_url
      ElMessage.success('头像已更新')
    }
  } catch { ElMessage.error('上传失败') }
  e.target.value = ''
}

function handleLogout() {
  sessionStorage.removeItem('token')
  sessionStorage.removeItem('userInfo')
  router.push('/admin/login')
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  height: calc(100vh - 16px);
  margin: 8px;
  background: #f5f0eb;
  position: relative;
  border-radius: 8px;
  overflow: hidden;
}

.admin-sidebar {
  width: 230px;
  background: #1a2634;
  color: #fff;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  margin-right: 10px;
}

.sidebar-header {
  padding: 22px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.sidebar-header h2 {
  margin: 0;
  font-size: 19px;
  color: #d4a24c;
}

.sidebar-nav {
  flex: 1;
  padding: 10px 0;
  display: flex;
  flex-direction: column;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  color: #b0b8c1;
  text-decoration: none;
  font-size: 15px;
  transition: all 0.2s;
}
.nav-item:hover {
  background: rgba(255,255,255,0.08);
  color: #fff;
}
.nav-item.active {
  background: rgba(212,162,76,0.15);
  color: #d4a24c;
  border-right: 3px solid #d4a24c;
}

.nav-divider {
  margin: 6px 14px;
  border-top: 1px solid rgba(255,255,255,0.1);
}

.admin-main {
  flex: 1;
  padding: 10px;
  overflow-y: auto;
}

/* 浮动头像 + 下拉菜单 */
.floating-avatar {
  position: fixed;
  top: 16px;
  right: 22px;
  z-index: 100;
}
.avatar-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 20px;
  transition: background 0.15s;
}
.avatar-trigger:hover { background: rgba(255,255,255,0.6); }
.avatar-name {
  font-size: 13px;
  color: #2C3E50;
  font-weight: 500;
}
</style>
