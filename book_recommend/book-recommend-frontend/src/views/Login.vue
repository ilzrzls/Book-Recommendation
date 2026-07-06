<template>
  <div class="auth-page">
    <div class="auth-card">
      <h2 class="auth-title">登录 BookRec</h2>
      <p class="auth-subtitle">基于知识图谱的个性化荐书系统</p>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="0" size="large">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleLogin" style="width: 100%">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="auth-footer">
        <span>还没有账号？</span>
        <router-link to="/register">立即注册</router-link>
      </div>
      <div class="auth-divider">
        <span>—————— 或 ——————</span>
      </div>
      <div class="admin-link">
        <router-link to="/admin/login" class="admin-btn">
          <el-icon><Setting /></el-icon> 管理员登录
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const formRef = ref(null)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await userStore.login(form.username, form.password)
    if (res.code === 200) {
      ElMessage.success('登录成功！')
      // Bug1 fix: 如果从阅读器拦截跳转来的，回到原页码
      const ret = sessionStorage.getItem('reader_return')
      if (ret) {
        try { const r = JSON.parse(ret); sessionStorage.removeItem('reader_return'); router.push(`/read/${r.bookId}?page=${r.page}`); return } catch {}
      }
      router.push('/')
    } else {
      ElMessage.error(res.message || '登录失败')
    }
  } catch (e) {
    ElMessage.error('登录失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #2C3E50 0%, #2E4A3A 100%);
}

.auth-card {
  background: #F5F0EB;
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}

.auth-title {
  text-align: center;
  color: #2C3E50;
  font-size: 24px;
  margin-bottom: 8px;
}

.auth-subtitle {
  text-align: center;
  color: #999;
  font-size: 14px;
  margin-bottom: 30px;
}

.auth-footer {
  text-align: center;
  font-size: 14px;
  color: #888;
}
.auth-footer a {
  color: #D4A24C;
  margin-left: 4px;
}

.auth-divider {
  text-align: center;
  margin: 20px 0 8px;
  font-size: 12px;
  color: #ccc;
}
.admin-link {
  text-align: center;
}
.admin-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 24px;
  border: 1px solid #2C3E50;
  border-radius: 8px;
  color: #2C3E50;
  font-size: 14px;
  text-decoration: none;
  transition: all 0.2s;
}
.admin-btn:hover {
  background: #2C3E50;
  color: #D4A24C;
}
.mock-hint {
  text-align: center;
  margin-top: 16px;
  font-size: 12px;
  color: #bbb;
}
</style>
