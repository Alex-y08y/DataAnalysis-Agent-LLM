import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, getUserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)
  const permissions = ref([])

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin')

  async function loginAction(credentials) {
    const res = await login(credentials)
    token.value = res.token
    localStorage.setItem('token', res.token)
    await fetchUserInfo()
    return res
  }

  async function fetchUserInfo() {
    try {
      const res = await getUserInfo()
      userInfo.value = res.user
      permissions.value = res.permissions || []
    } catch (e) {
      logout()
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    permissions.value = []
    localStorage.removeItem('token')
  }

  function hasPermission(perm) {
    return permissions.value.includes(perm) || userInfo.value?.role === 'admin'
  }

  return { token, userInfo, permissions, isLoggedIn, isAdmin, loginAction, fetchUserInfo, logout, hasPermission }
})

export const useChatStore = defineStore('chat', () => {
  const sessions = ref([])
  const currentSessionId = ref(null)
  const messages = ref([])
  const isProcessing = ref(false)
  const analysisSteps = ref([])

  const currentSession = computed(() => {
    return sessions.value.find(s => s.id === currentSessionId.value)
  })

  const currentMessages = computed(() => messages.value)

  function setCurrentSession(id) {
    currentSessionId.value = id
  }

  function addMessage(msg) {
    messages.value.push(msg)
  }

  function clearMessages() {
    messages.value = []
  }

  function addStep(step) {
    analysisSteps.value.push(step)
  }

  function clearSteps() {
    analysisSteps.value = []
  }

  function updateStep(id, data) {
    const idx = analysisSteps.value.findIndex(s => s.id === id)
    if (idx !== -1) {
      analysisSteps.value[idx] = { ...analysisSteps.value[idx], ...data }
    }
  }

  return {
    sessions, currentSessionId, messages, isProcessing, analysisSteps,
    currentSession, currentMessages,
    setCurrentSession, addMessage, clearMessages,
    addStep, clearSteps, updateStep,
  }
})

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const loading = ref(false)

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return { sidebarCollapsed, loading, toggleSidebar }
})
