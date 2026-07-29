<template>
  <div class="chat-page">
    <div class="chat-layout">
      <!-- Session Sidebar -->
      <div class="session-sidebar">
        <div class="session-header">
          <h3>对话列表</h3>
          <el-button type="primary" :icon="Plus" circle size="small" @click="newSession" />
        </div>
        <div class="session-list">
          <div
            v-for="session in sessions"
            :key="session.id"
            class="session-item"
            :class="{ active: session.id === currentSessionId }"
            @click="switchSession(session.id)"
          >
            <div class="session-name">{{ session.name || '新对话' }}</div>
            <div class="session-time">{{ formatDate(session.updated_at) }}</div>
            <el-button
              v-if="session.id === currentSessionId"
              class="delete-btn"
              :icon="Delete"
              circle
              size="small"
              text
              type="danger"
              @click.stop="handleDeleteSession(session.id)"
            />
          </div>
        </div>
      </div>

      <!-- Chat Main Area -->
      <div class="chat-main">
        <!-- Messages -->
        <div class="messages-container" ref="messagesRef">
          <div v-if="messages.length === 0" class="welcome-placeholder">
            <el-icon :size="64" color="#c0c4cc"><ChatDotSquare /></el-icon>
            <h3>开始数据分析</h3>
            <p>输入自然语言描述你的数据分析需求，AI Agent 将自动完成数据查询、分析和可视化。</p>
            <div class="suggestions">
              <el-tag
                v-for="s in suggestions"
                :key="s"
                class="suggestion-tag"
                @click="sendSuggestion(s)"
              >
                {{ s }}
              </el-tag>
            </div>
          </div>
          <div v-for="(msg, idx) in messages" :key="idx" class="message-wrapper">
            <ChatMessage
              :message="msg"
              :is-user="msg.role === 'user'"
              @copy="handleCopy(msg)"
            />
            <!-- Analysis steps timeline shown after assistant messages -->
            <div v-if="msg.role === 'assistant' && msg.steps && msg.steps.length" class="timeline-wrapper">
              <AnalysisTimeline :steps="msg.steps" />
            </div>
          </div>
          <div v-if="isProcessing" class="message-wrapper">
            <div class="message assistant-message">
              <div class="avatar agent-avatar">
                <el-icon><Monitor /></el-icon>
              </div>
              <div class="content">
                <div class="typing-indicator">
                  <span>分析中</span>
                  <span class="dots"><span>.</span><span>.</span><span>.</span></span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Analysis Steps Panel (right side) -->
        <div v-if="showStepsPanel && analysisSteps.length" class="steps-panel">
          <div class="steps-header">
            <h4>执行链路</h4>
            <el-button text :icon="Close" size="small" @click="showStepsPanel = false" />
          </div>
          <AnalysisTimeline :steps="analysisSteps" detailed />
        </div>

        <!-- Input Area -->
        <div class="input-area">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="3"
            :disabled="isProcessing"
            placeholder="输入你的数据分析需求，例如：统计最近30天各地区的销售额并绘制柱状图..."
            resize="none"
            @keydown.enter.prevent="handleSend"
          />
          <div class="input-actions">
            <div class="action-left">
              <el-tooltip content="清除对话" placement="top">
                <el-button :icon="Delete" circle text @click="clearChat" />
              </el-tooltip>
            </div>
            <div class="action-right">
              <el-button
                type="primary"
                :icon="Promotion"
                :loading="isProcessing"
                :disabled="!inputText.trim()"
                @click="handleSend"
              >
                发送
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, ChatDotSquare, Monitor, Promotion, Close } from '@element-plus/icons-vue'
import { useChatStore, useUserStore } from '@/store'
import { sendMessage, getSessions, getChatHistory, createSession, deleteSession } from '@/api/chat'
import ChatMessage from '@/components/ChatMessage.vue'
import AnalysisTimeline from '@/components/AnalysisTimeline.vue'
import { formatDate, copyToClipboard } from '@/utils/format'

const router = useRouter()
const chatStore = useChatStore()
const userStore = useUserStore()

const messagesRef = ref(null)
const inputText = ref('')
const showStepsPanel = ref(false)

const {
  sessions, currentSessionId, messages, isProcessing, analysisSteps,
  setCurrentSession, addMessage, clearMessages, clearSteps,
} = chatStore

const suggestions = [
  '统计最近30天的销售数据并绘制趋势图',
  '分析各产品类别的销售额占比',
  '按月统计用户增长趋势',
  '找出销售额Top10的区域并制作柱状图',
]

onMounted(async () => {
  if (!userStore.isLoggedIn) {
    router.push('/login')
    return
  }
  await loadSessions()
  if (sessions.length > 0) {
    switchSession(sessions[0].id)
  }
})

async function loadSessions() {
  try {
    const res = await getSessions()
    sessions.length = 0
    sessions.push(...(res.sessions || res.data || []))
  } catch (e) {
    console.error('加载会话失败', e)
  }
}

async function switchSession(id) {
  setCurrentSession(id)
  clearMessages()
  clearSteps()
  try {
    const res = await getChatHistory(id)
    const history = res.messages || res.data || []
    history.forEach(msg => addMessage(msg))
  } catch (e) {
    console.error('加载历史消息失败', e)
  }
  scrollToBottom()
}

async function newSession() {
  try {
    const res = await createSession({ name: `新对话 ${sessions.length + 1}` })
    const session = res.session || res.data || { id: res.id, name: res.name }
    sessions.unshift(session)
    setCurrentSession(session.id)
    clearMessages()
    clearSteps()
  } catch (e) {
    console.error('创建会话失败', e)
  }
}

async function handleDeleteSession(id) {
  try {
    await ElMessageBox.confirm('确定删除此对话？', '提示', { type: 'warning' })
    await deleteSession(id)
    const idx = sessions.findIndex(s => s.id === id)
    sessions.splice(idx, 1)
    if (currentSessionId.value === id) {
      if (sessions.length > 0) {
        switchSession(sessions[0].id)
      } else {
        clearMessages()
        clearSteps()
        setCurrentSession(null)
      }
    }
    ElMessage.success('已删除')
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || isProcessing.value) return

  inputText.value = ''
  showStepsPanel.value = true

  // Add user message
  addMessage({ role: 'user', content: text, timestamp: new Date().toISOString() })

  chatStore.isProcessing = true
  clearSteps()
  const currentSteps = []

  try {
    const res = await sendMessage({
      session_id: currentSessionId.value,
      content: text,
    })

    const result = res.data || res

    // Add assistant message
    addMessage({
      role: 'assistant',
      content: result.answer || result.content || '',
      steps: result.steps || [],
      charts: result.charts || [],
      tables: result.tables || [],
      sql: result.sql || '',
      timestamp: new Date().toISOString(),
    })

    // Update analysis steps
    if (result.steps) {
      result.steps.forEach(s => addStep(s))
    }
  } catch (e) {
    addMessage({
      role: 'assistant',
      content: '抱歉，分析过程中遇到错误，请稍后重试。',
      isError: true,
      timestamp: new Date().toISOString(),
    })
  } finally {
    chatStore.isProcessing = false
    scrollToBottom()
  }
}

function sendSuggestion(text) {
  inputText.value = text
  handleSend()
}

function clearChat() {
  clearMessages()
  clearSteps()
}

async function handleCopy(msg) {
  const text = msg.content || JSON.stringify(msg)
  await copyToClipboard(text)
  ElMessage.success('已复制')
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.chat-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.session-sidebar {
  width: 260px;
  border-right: 1px solid #e4e7ed;
  background: #fff;
  display: flex;
  flex-direction: column;
}
.session-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}
.session-header h3 {
  margin: 0;
  font-size: 16px;
}
.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.session-item {
  display: flex;
  flex-direction: column;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  position: relative;
  transition: background 0.2s;
}
.session-item:hover {
  background: #f5f7fa;
}
.session-item.active {
  background: #ecf5ff;
}
.session-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
}
.session-time {
  font-size: 12px;
  color: #999;
}
.delete-btn {
  position: absolute;
  right: 8px;
  top: 8px;
  opacity: 0;
}
.session-item:hover .delete-btn {
  opacity: 1;
}
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f5f7fa;
}
.welcome-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #606266;
}
.welcome-placeholder h3 {
  margin: 16px 0 8px;
  font-size: 20px;
}
.welcome-placeholder p {
  color: #909399;
  max-width: 480px;
  text-align: center;
  line-height: 1.6;
  margin-bottom: 24px;
}
.suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  max-width: 500px;
}
.suggestion-tag {
  cursor: pointer;
  padding: 4px 8px;
}
.message-wrapper {
  max-width: 800px;
  margin: 0 auto 16px;
}
.timeline-wrapper {
  margin-top: 8px;
  padding-left: 56px;
}
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #909399;
  font-size: 14px;
}
.dots span {
  animation: blink 1.4s infinite both;
}
.dots span:nth-child(2) { animation-delay: 0.2s; }
.dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink {
  0%, 80%, 100% { opacity: 0; }
  40% { opacity: 1; }
}
.steps-panel {
  width: 320px;
  border-left: 1px solid #e4e7ed;
  background: #fff;
  overflow-y: auto;
}
.steps-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}
.steps-header h4 {
  margin: 0;
  font-size: 14px;
}
.input-area {
  padding: 16px 24px;
  background: #fff;
  border-top: 1px solid #e4e7ed;
}
.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
</style>
