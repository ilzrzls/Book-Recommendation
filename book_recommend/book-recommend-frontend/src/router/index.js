import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { title: '首页 - BookRec' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录 - BookRec' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { title: '注册 - BookRec' }
  },
  {
    path: '/book/:id',
    name: 'BookDetail',
    component: () => import('../views/BookDetail.vue'),
    meta: { title: '图书详情 - BookRec' }
  },
  {
    path: '/read/:id',
    name: 'Reader',
    component: () => import('../views/Reader.vue'),
    meta: { title: '在线阅读 - BookRec' }
  },
  {
    path: '/shelves',
    name: 'Shelves',
    component: () => import('../views/Shelves.vue'),
    meta: { title: '我的书架 - BookRec' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { title: '个人中心 - BookRec' }
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('../views/Search.vue'),
    meta: { title: '搜索 - BookRec' }
  },
  {
    path: '/write',
    name: 'TutuWrite',
    component: () => import('../views/TutuWrite.vue'),
    meta: { title: '图图写作 - BookRec' }
  },
  {
    path: '/graph',
    name: 'GraphSearch',
    component: () => import('../views/GraphSearch.vue'),
    meta: { title: '知识图谱 - BookRec' }
  },
  // ── 管理员后台 ──
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('../views/admin/AdminLogin.vue'),
    meta: { title: '管理后台登录 - BookRec' }
  },
  {
    path: '/admin',
    component: () => import('../views/admin/AdminLayout.vue'),
    meta: { requiresAdmin: true },
    children: [
      { path: '', name: 'Dashboard', component: () => import('../views/admin/Dashboard.vue'), meta: { title: '仪表盘 - 管理后台' } },
      { path: 'books', name: 'AdminBooks', component: () => import('../views/admin/BooksManager.vue'), meta: { title: '图书管理 - 管理后台' } },
      { path: 'users', name: 'AdminUsers', component: () => import('../views/admin/UsersManager.vue'), meta: { title: '用户管理 - 管理后台' } },
      { path: 'comments', name: 'AdminComments', component: () => import('../views/admin/CommentsManager.vue'), meta: { title: '评论管理 - 管理后台' } },
      { path: 'graph', name: 'AdminGraph', component: () => import('../views/admin/KnowledgeGraph.vue'), meta: { title: '知识图谱 - 管理后台' } },
    ]
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫：设置页面标题 + 管理员权限检查
router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'BookRec - 个性化荐书系统'

  // 检查管理员权限
  if (to.matched.some(r => r.meta.requiresAdmin)) {
    const token = sessionStorage.getItem('token')
    const userInfo = JSON.parse(sessionStorage.getItem('userInfo') || '{}')
    if (!token || userInfo.role !== 'admin') {
      // 无权限，跳转管理员登录页
      next('/admin/login')
      return
    }
  }
  next()
})

export default router
