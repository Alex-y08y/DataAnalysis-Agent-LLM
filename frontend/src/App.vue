<template>
  <div class="app-container">
    <template v-if="!isLoginPage">
      <Sidebar />
      <div class="main-content" :class="{ collapsed: appStore.sidebarCollapsed }">
        <router-view />
      </div>
    </template>
    <template v-else>
      <router-view />
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from '@/components/Sidebar.vue'
import { useAppStore } from '@/store'

const route = useRoute()
const appStore = useAppStore()

const isLoginPage = computed(() => route.path === '/login')
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}
.main-content {
  flex: 1;
  margin-left: 220px;
  overflow-y: auto;
  background-color: #f5f7fa;
  transition: margin-left 0.3s ease;
}
.main-content.collapsed {
  margin-left: 64px;
}
</style>
