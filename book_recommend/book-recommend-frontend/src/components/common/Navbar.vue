<template>
  <header class="navbar">
    <div class="navbar-inner">
      <router-link to="/" class="logo">
        <el-icon :size="24"><Reading /></el-icon>
        <span class="logo-text">BookRec</span>
      </router-link>

      <div class="search-bar">
        <el-input v-model="keyword" placeholder="搜索书名..." prefix-icon="Search" size="large" @keyup.enter="handleSearch" />
      </div>

      <nav class="nav-links">
        <router-link to="/" class="nav-item">首页</router-link>
        <router-link to="/shelves" class="nav-item">书架</router-link>
        <router-link to="/graph" class="nav-item">图谱</router-link>
        <router-link to="/write" class="nav-item">写作</router-link>
        <!-- 分类按钮 -->
        <el-popover placement="bottom" :width="380" trigger="click">
          <template #reference>
            <span class="nav-item nav-category-btn">分类</span>
          </template>
          <div class="category-panel">
            <!-- 第一级：免费/付费（互斥） -->
            <div class="cp-section">
              <span class="cp-section-title">价格</span>
              <div class="cp-price-tags">
                <span class="price-tag" :class="{ active: priceFilter === 'free' }" @click="togglePrice('free')">免费</span>
                <span class="price-tag" :class="{ active: priceFilter === 'paid' }" @click="togglePrice('paid')">付费</span>
              </div>
            </div>
            <!-- 第二级：题材标签（可多选，年代标签排最前） -->
            <div class="cp-section">
              <div class="cp-header"><span>题材（可多选）</span><el-button size="small" text @click="selectedTags=[]">清空</el-button></div>
              <div class="cp-tags">
                <el-check-tag v-for="tag in sortedTags" :key="tag.id" :checked="selectedTags.includes(tag.name)" @change="(c) => toggleTag(tag.name, c)" size="small">{{ tag.name }}</el-check-tag>
              </div>
            </div>
            <div class="cp-footer">
              <el-button size="small" text @click="clearAll">清空全部</el-button>
              <el-button size="small" type="primary" @click="searchByTags" :disabled="!priceFilter && selectedTags.length===0">
                搜索
              </el-button>
            </div>
          </div>
        </el-popover>
      </nav>

      <div class="user-area">
        <template v-if="userStore.isLoggedIn">
          <el-dropdown trigger="click">
            <span class="user-avatar">
              <el-avatar :size="36" :src="getAvatarUrl(userStore.userInfo?.avatar, userStore.username)" />
              <span class="username">{{ userStore.username }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-if="userStore.userInfo?.role==='admin'" @click="$router.push('/admin')"><el-icon><Setting /></el-icon> 管理后台</el-dropdown-item>
                <el-dropdown-item @click="$router.push('/profile')"><el-icon><User /></el-icon> 个人中心</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout"><el-icon><SwitchButton /></el-icon> 退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <el-button type="primary" size="small" @click="$router.push('/login')">登录</el-button>
          <el-button size="small" @click="$router.push('/register')">注册</el-button>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { ElMessage } from 'element-plus'
import { getAvatarUrl } from '../../utils/avatar'
import request from '../../api/request'

const router = useRouter()
const userStore = useUserStore()
const keyword = ref('')
const allTags = ref([])
const selectedTags = ref([])
const priceFilter = ref('')  // '' | 'free' | 'paid'
const ERA_NAMES = ['古典文学', '现代文学', '当代文学', '外国文学']
const sortedTags = computed(() => {
  const era = allTags.value.filter(t => ERA_NAMES.includes(t.name))
  const rest = allTags.value.filter(t => !ERA_NAMES.includes(t.name))
  return [...era, ...rest]
})

onMounted(async () => {
  try { const r = await request.get('/tags'); if (r.code===200) { allTags.value = r.data.items } } catch {}
})

function togglePrice(type) {
  priceFilter.value = priceFilter.value === type ? '' : type
}
function toggleTag(name, checked) {
  if (checked) selectedTags.value.push(name)
  else selectedTags.value = selectedTags.value.filter(t => t !== name)
}
function clearAll() {
  selectedTags.value = []
  priceFilter.value = ''
}
function searchByTags() {
  const query = {}
  if (selectedTags.value.length) query.tags = selectedTags.value.join(',')
  if (priceFilter.value) query.price = priceFilter.value
  if (Object.keys(query).length) router.push({ path: '/search', query })
}
function handleSearch() {
  if (keyword.value.trim()) router.push({ path: '/search', query: { keyword: keyword.value.trim() } })
}
async function handleLogout() { await userStore.logout(); ElMessage.success('已退出登录'); router.push('/') }
</script>

<style scoped>
.navbar {
  background: #2C3E50;
  color: #fff;
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.navbar-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  align-items: center;
  height: 60px;
  gap: 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #D4A24C;
  font-size: 20px;
  font-weight: bold;
  text-decoration: none;
  flex-shrink: 0;
}

.search-bar {
  flex: 1;
  max-width: 480px;
}

.nav-links {
  display: flex;
  gap: 8px;
}

.nav-item {
  color: #ddd;
  padding: 6px 16px;
  border-radius: 4px;
  transition: all 0.3s;
}
.nav-item:hover, .nav-item.router-link-active {
  color: #D4A24C;
  background: rgba(255,255,255,0.1);
}
.nav-category-btn { cursor: pointer; }

.category-panel { padding: 8px; }
.cp-section { margin-bottom: 10px; }
.cp-section-title { font-size: 13px; color: #666; font-weight: 600; display: block; margin-bottom: 6px; }
.cp-price-tags { display: flex; gap: 8px; }
.price-tag {
  padding: 4px 14px; border-radius: 14px; font-size: 13px; cursor: pointer;
  border: 1px solid #d9d9d9; background: #fafafa; transition: all 0.2s; user-select: none;
}
.price-tag:hover { border-color: #D4A24C; color: #D4A24C; }
.price-tag.active { background: #D4A24C; border-color: #D4A24C; color: #fff; }
.cp-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 13px; color: #666; }
.cp-tags { display: flex; flex-wrap: wrap; gap: 6px; max-height: 200px; overflow-y: auto; }
.cp-footer { margin-top: 10px; display: flex; justify-content: space-between; align-items: center; }

.user-area {
  flex-shrink: 0;
}

.user-avatar {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #ddd;
}

.username {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.6;
  display: inline-block;
  vertical-align: middle;
}
</style>
