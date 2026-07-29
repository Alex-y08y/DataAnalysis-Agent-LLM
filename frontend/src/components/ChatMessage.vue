<template>
  <div class="chat-message" :class="{ 'user-message': isUser, 'assistant-message': !isUser, 'error-message': message.isError }">
    <div class="avatar" :class="{ 'user-avatar': isUser, 'agent-avatar': !isUser }">
      <el-icon v-if="isUser"><User /></el-icon>
      <el-icon v-else><Monitor /></el-icon>
    </div>
    <div class="message-body">
      <div class="message-sender">
        <span class="sender-name">{{ isUser ? '你' : 'AI 分析助手' }}</span>
        <span class="message-time">{{ formatDate(message.timestamp) }}</span>
        <el-button class="copy-btn" text size="small" :icon="CopyDocument" @click="$emit('copy')">复制</el-button>
      </div>
      <div class="message-content">
        <!-- Text content with markdown support -->
        <div v-if="message.content" class="text-content" v-html="renderMarkdown(message.content)"></div>

        <!-- SQL code block -->
        <div v-if="message.sql" class="sql-block">
          <div class="sql-header">
            <el-icon><Monitor /></el-icon>
            <span>SQL 查询</span>
            <el-button text size="small" :icon="CopyDocument" @click="copyText(message.sql)">复制SQL</el-button>
          </div>
          <pre class="sql-code"><code>{{ message.sql }}</code></pre>
        </div>

        <!-- Data table -->
        <div v-if="message.tables && message.tables.length" class="data-tables">
          <div v-for="(table, idx) in message.tables" :key="idx" class="data-table">
            <div class="table-title" v-if="table.title">{{ table.title }}</div>
            <el-table :data="table.data || []" :max-height="400" border stripe size="small" style="width: 100%">
              <el-table-column v-for="col in (table.columns || [])" :key="col" :prop="col" :label="col" min-width="100" show-overflow-tooltip />
            </el-table>
            <div class="table-meta" v-if="table.rows_count">
              共 {{ table.rows_count }} 条记录
            </div>
          </div>
        </div>

        <!-- Charts -->
        <div v-if="message.charts && message.charts.length" class="message-charts">
          <div v-for="(chart, idx) in message.charts" :key="idx" class="chart-item">
            <ChartView :chart-data="chart" :height="300" />
          </div>
        </div>
      </div>

      <!-- Steps timeline for assistant messages -->
      <div v-if="!isUser && message.steps && message.steps.length" class="inline-steps">
        <AnalysisTimeline :steps="message.steps" compact />
      </div>
    </div>
  </div>
</template>

<script setup>
import { User, Monitor, CopyDocument } from '@element-plus/icons-vue'
import ChartView from './ChartView.vue'
import AnalysisTimeline from './AnalysisTimeline.vue'
import { formatDate, copyToClipboard } from '@/utils/format'
import MarkdownIt from 'markdown-it'

const props = defineProps({
  message: { type: Object, required: true },
  isUser: { type: Boolean, default: false },
})

const emit = defineEmits(['copy'])

const md = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true,
})

function renderMarkdown(content) {
  if (!content) return ''
  return md.render(content)
}

async function copyText(text) {
  await copyToClipboard(text)
}
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}
.user-message {
  flex-direction: row-reverse;
}
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 18px;
}
.user-avatar {
  background: #409eff;
  color: #fff;
}
.agent-avatar {
  background: #67c23a;
  color: #fff;
}
.message-body {
  max-width: 85%;
  background: #fff;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.user-message .message-body {
  background: #ecf5ff;
}
.error-message .message-body {
  background: #fef0f0;
}
.message-sender {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.sender-name {
  font-weight: 600;
  font-size: 14px;
}
.message-time {
  font-size: 12px;
  color: #909399;
}
.copy-btn {
  margin-left: auto;
}
.text-content {
  line-height: 1.7;
  font-size: 14px;
  color: #303133;
}
:deep(.text-content p) {
  margin: 4px 0;
}
:deep(.text-content code) {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
:deep(.text-content pre) {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 13px;
}
:deep(.text-content pre code) {
  background: transparent;
  color: inherit;
  padding: 0;
}
:deep(.text-content table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}
:deep(.text-content th, .text-content td) {
  border: 1px solid #e4e7ed;
  padding: 8px 12px;
  text-align: left;
}
:deep(.text-content th) {
  background: #f5f7fa;
}
.sql-block {
  margin-top: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}
.sql-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  font-size: 13px;
  font-weight: 500;
}
.sql-code {
  margin: 0;
  padding: 12px;
  background: #1e1e1e;
  color: #d4d4d4;
  overflow-x: auto;
  font-size: 13px;
}
.data-tables {
  margin-top: 12px;
}
.data-table {
  margin-bottom: 12px;
}
.table-title {
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 14px;
}
.table-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  text-align: right;
}
.message-charts {
  margin-top: 12px;
}
.chart-item {
  margin-bottom: 12px;
}
.inline-steps {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}
</style>
