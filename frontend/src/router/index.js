import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', noAuth: true },
  },
  {
    path: '/',
    name: 'Chat',
    component: () => import('@/views/Chat.vue'),
    meta: { title: '对话分析', icon: 'ChatDotSquare' },
  },
  {
    path: '/datasources',
    name: 'DataSource',
    component: () => import('@/views/DataSource.vue'),
    meta: { title: '数据源管理', icon: 'DataBoard' },
  },
  {
    path: '/knowledge',
    name: 'KnowledgeBase',
    component: () => import('@/views/KnowledgeBase.vue'),
    meta: { title: '知识库管理', icon: 'Notebook' },
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/views/Reports.vue'),
    meta: { title: '报表中心', icon: 'Document' },
  },
  {
    path: '/tasks',
    name: 'TaskHistory',
    component: () => import('@/views/TaskHistory.vue'),
    meta: { title: '任务管理', icon: 'List' },
  },
  {
    path: '/admin/users',
    name: 'UserManage',
    component: () => import('@/views/UserManage.vue'),
    meta: { title: '用户管理', icon: 'User', admin: true },
  },
  {
    path: '/admin/logs',
    name: 'AuditLog',
    component: () => import('@/views/AuditLog.vue'),
    meta: { title: '审计日志', icon: 'Reading', admin: true },
  },
  {
    path: '/admin/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置', icon: 'Setting', admin: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.noAuth) {
    next()
  } else if (!token) {
    next('/login')
  } else {
    next()
  }
})

export default router
