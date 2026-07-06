import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

import App from './App.vue'
import router from './router'
import { ElMessage } from 'element-plus'
// 导入 Mock 拦截器（开发模式下拦截 Axios 请求返回 Mock 数据）
import './mock'

// 全局缩短消息弹窗时间（默认3秒→1.5秒）
const _msg = ElMessage
const patchMsg = (fn) => (...args) => {
  const opt = typeof args[0] === 'string' ? { message: args[0] } : (args[0] || {})
  return fn({ duration: 1500, ...opt }, args[1])
}
ElMessage.success = patchMsg(_msg.success)
ElMessage.error = patchMsg(_msg.error)
ElMessage.warning = patchMsg(_msg.warning)
ElMessage.info = patchMsg(_msg.info)

const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
// 全局消息弹窗时间缩短为1.5秒
app.config.globalProperties.$ELEMENT = { duration: 1500 }
app.mount('#app')
