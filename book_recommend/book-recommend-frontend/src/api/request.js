import axios from 'axios'
import { ElMessage } from 'element-plus'

const USE_MOCK = false // 已连接真实后端

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

// Request interceptor - attach token (sessionStorage: 关标签页自动登出)
request.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
request.interceptors.response.use(
  (response) => {
    const data = response.data
    if (data.code && data.code !== 200) {
      ElMessage.error(data.message || 'Request failed')
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  (error) => {
    if (error.response?.status === 401) {
      // 只有原本已登录（有token）才跳登录页；游客正常浏览
      const hadToken = sessionStorage.getItem('token')
      if (hadToken) {
        sessionStorage.removeItem('token')
        sessionStorage.removeItem('userInfo')
        ElMessage.error('登录已过期，请重新登录')
        window.location.href = '/login'
      }
      // 游客遇到401不跳转，静默处理
    } else if (error.response?.status === 403) {
      // 403（试读上限）不弹toast，由页面自己处理（如Reader的登录弹窗）
    } else {
      ElMessage.error(error.message || 'Network error')
    }
    return Promise.reject(error)
  }
)

export default request
export { USE_MOCK }
