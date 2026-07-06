<template>
  <div class="admin-login-page">
    <div class="login-card">
      <h2>⚙️ 管理后台</h2>
      <p class="subtitle">BookRec 荐书系统</p>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="0" size="large">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="管理员账号" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleLogin" style="width:100%">
            登录后台
          </el-button>
        </el-form-item>
      </el-form>

      <div class="footer-link">
        <router-link to="/login">← 返回用户登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import request from '../../api/request'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const formRef = ref(null)

const form = reactive({
  username: 'admin',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入管理员账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await request.post('/admin/login', { username: form.username, password: form.password })
    if (res.code === 200) {
      sessionStorage.setItem('token', res.data.access_token)
      sessionStorage.setItem('userInfo', JSON.stringify(res.data.user))
      ElMessage.success('管理员登录成功')
      router.push('/admin')
    } else {
      ElMessage.error(res.message || '登录失败')
    }
  } catch (e) {
    ElMessage.error('登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.admin-login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a2634 0%, #2C3E50 50%, #2E4A3A 100%);
}

.login-card {
  background: #F5F0EB;
  border-radius: 16px;
  padding: 44px 36px;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}

h2 {
  text-align: center;
  color: #2C3E50;
  font-size: 22px;
  margin-bottom: 4px;
}

.subtitle {
  text-align: center;
  color: #999;
  font-size: 13px;
  margin-bottom: 28px;
}

.footer-link {
  text-align: center;
  margin-top: 16px;
}
.footer-link a {
  color: #888;
  font-size: 13px;
}
.footer-link a:hover {
  color: #D4A24C;
}
</style>
