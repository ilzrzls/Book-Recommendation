<template>
  <div id="app">
    <Navbar v-if="!isAuthPage" />
    <main :class="{ 'main-content': !isAuthPage }">
      <router-view />
    </main>
    <Footer v-if="!isAuthPage" />

    <!-- AI 聊天助手：全站入口，路由感知图书上下文 -->
    <ChatWidget v-if="!isAuthPage" :book-id="chatBookId" :book-title="chatBookTitle" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from './components/common/Navbar.vue'
import Footer from './components/common/Footer.vue'
import ChatWidget from './components/chat/ChatWidget.vue'
import { useBookStore } from './stores/book'

const route = useRoute()
const bookStore = useBookStore()
const isAdminPage = computed(() => {
  const n = route.name
  return n === 'AdminLogin' || n === 'Dashboard' || (n && n.startsWith('Admin'))
})
const isAuthPage = computed(() => ['Login', 'Register', 'AdminLogin'].includes(route.name) || isAdminPage.value)

// 路由感知：在图书详情页 / 在线阅读页时传递图书上下文
const chatBookId = computed(() => {
  if (route.name === 'BookDetail' || route.name === 'Reader') return Number(route.params.id)
  return null
})
const chatBookTitle = computed(() => {
  if (route.name === 'BookDetail' || route.name === 'Reader') return bookStore.currentBook?.title || ''
  return ''
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  background-color: #F5F0EB;
  color: #2C3E50;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  max-width: 100%;
  margin: 0 auto;
  padding: 16px 36px;
  width: 100%;
}

a {
  text-decoration: none;
  color: inherit;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: #F5F0EB;
}
::-webkit-scrollbar-thumb {
  background: #D4A24C;
  border-radius: 3px;
}
</style>
