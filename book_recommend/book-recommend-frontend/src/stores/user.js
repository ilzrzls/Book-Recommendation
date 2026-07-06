import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '../api/auth'

export const useUserStore = defineStore('user', () => {
  // sessionStorage: 关闭标签页自动清除，下次打开为未登录状态
  const token = ref(sessionStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(sessionStorage.getItem('userInfo') || 'null'))
  const profile = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '游客')

  async function login(username, password) {
    const res = await authAPI.login(username, password)
    if (res.code === 200) {
      token.value = res.data.access_token
      userInfo.value = res.data.user
      sessionStorage.setItem('token', res.data.access_token)
      sessionStorage.setItem('userInfo', JSON.stringify(res.data.user))
    }
    return res
  }

  async function register(username, password) {
    const res = await authAPI.register(username, password)
    return res
  }

  async function logout() {
    // 清空本地状态
    token.value = ''
    userInfo.value = null
    profile.value = null
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('userInfo')
    // 通知后端清除 Flask session cookie
    try { await authAPI.logout() } catch {}
    // 刷新回首页，此时 session cookie 已清除
    window.location.href = '/'
  }

  async function fetchProfile() {
    const res = await authAPI.getProfile()
    if (res.code === 200) {
      profile.value = res.data
    }
    return res
  }

  async function updateUsername(newName) {
    const res = await authAPI.updateProfile({ username: newName })
    if (res.code === 200) {
      // 同步所有本地状态
      if (userInfo.value) {
        userInfo.value.username = newName
        sessionStorage.setItem('userInfo', JSON.stringify(userInfo.value))
      }
      if (profile.value) {
        profile.value.username = newName
      }
    }
    return res
  }

  function updateAvatar(avatarUrl) {
    // 通过替换整个对象确保 Vue 响应式更新触发
    if (userInfo.value) {
      userInfo.value = { ...userInfo.value, avatar: avatarUrl }
      sessionStorage.setItem('userInfo', JSON.stringify(userInfo.value))
    }
    if (profile.value) {
      profile.value = { ...profile.value, avatar: avatarUrl }
    }
  }

  return { token, userInfo, profile, isLoggedIn, username, login, register, logout, fetchProfile, updateUsername, updateAvatar }
})
