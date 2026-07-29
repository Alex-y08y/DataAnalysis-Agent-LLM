<template>
  <div class="sidebar" :class="{ collapsed: appStore.sidebarCollapsed }">
    <div class="sidebar-header">
      <div class="logo" @click="router.push('/')">
        <el-icon :size="28" color="#409eff"><DataAnalysis /></el-icon>
        <span v-show="!appStore.sidebarCollapsed" class="logo-text">DataAgent</span>
      </div>
      <el-button
        class="collapse-btn"
        :icon="appStore.sidebarCollapsed ? Expand : Fold"
        text
        size="small"
        @click="appStore.toggleSidebar()"
      />
    </div>

    <el-menu
      :default-active="route.path"
      :collapse="appStore.sidebarCollapsed"
      :router="true"
      class="sidebar-menu"
      background-color="transparent"
    >
      <el-menu-item index="/">
        <el-icon><ChatDotSquare /></el-icon>
        <template #title>对话分析</template>
      </el-menu-item>
      <el-menu-item index="/datasources">
        <el-icon><DataBoard /></el-icon>
        <template #title>数据源管理</template>
      </el-menu-item>
      <el-menu-item index="/knowledge">
        <el-icon><Notebook /></el-icon>
        <template #title>知识库管理</template>
      </el-menu-item>
      <el-menu-item index="/reports">
        <el-icon><Document /></el-icon>
        <template #title>报表中心</template>
      </el-menu-item>
      <el-menu-item index="/tasks">
        <el-icon><List /></el-icon>
        <template #title>任务管理</template>
      </el-menu-item>

      <el-divider v-if="userStore.isAdmin" class="menu-divider" />

      <template v-if="userStore.isAdmin">
        <el-menu-item index="/admin/users">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/logs">
          <el-icon><Reading /></el-icon>
          <template #title>审计日志</template>
        </el-menu-item>
        <el-menu-item index="/admin/settings">
          <el-icon><Setting /></el-icon>
          <template #title>系统设置</template>
        </el-menu-item>
      </template>
    </el-menu>

    <div class="sidebar-footer">
      <el-dropdown trigger="click" placement="right">
        <div class="user-info">
          <el-avatar :size="32" :icon="UserFilled" />
          <div v-show="!appStore.sidebarCollapsed" class="user-detail">
            <div class="user-name">{{ userStore.userInfo?.username || '用户' }}</div>
            <div class="user-role">{{ userStore.userInfo?.role === 'admin' ? '管理员' : '用户' }}</div>
          </div>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="router.push('/admin/settings')">
              <el-icon><Setting /></el-icon>系统设置
            </el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">
              <el-icon><SwitchButton /></el-icon>退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  DataAnalysis, ChatDotSquare, DataBoard, Notebook, Document, List,
  User, Reading, Setting, Expand, Fold, UserFilled, SwitchButton,
} from '@element-plus/icons-vue'
import { useUserStore, useAppStore } from '@/store'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const appStore = useAppStore()

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定退出登录？', '提示', { type: 'info' })
    userStore.logout()
    router.push('/login')
    ElMessage.success('已退出')
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  width: 220px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  z-index: 100;
  overflow: hidden;
}
.sidebar.collapsed {
  width: 64px;
}
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: #303133;
  white-space: nowrap;
}
.collapse-btn {
  flex-shrink: 0;
}
.sidebar-menu {
  flex: 1;
  border-right: none;
  overflow-y: auto;
  padding: 8px 0;
}
:deep(.el-menu-item) {
  margin: 2px 8px;
  border-radius: 8px;
  height: 44px;
  line-height: 44px;
}
:deep(.el-menu-item.is-active) {
  background: #ecf5ff;
  color: #409eff;
  font-weight: 500;
}
:deep(.el-menu-item:hover) {
  background: #f5f7fa;
}
.menu-divider {
  margin: 4px 16px;
  border-color: #f0f0f0;
}
.sidebar-footer {
  border-top: 1px solid #f0f0f0;
  padding: 12px 16px;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px;
  border-radius: 8px;
  transition: background 0.2s;
}
.user-info:hover {
  background: #f5f7fa;
}
.user-detail {
  flex: 1;
  min-width: 0;
}
.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-role {
  font-size: 12px;
  color: #909399;
}
</style>
