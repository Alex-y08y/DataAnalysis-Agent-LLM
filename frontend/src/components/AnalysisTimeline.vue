<template>
  <div class="analysis-timeline" :class="{ compact, detailed }">
    <div class="timeline-title" v-if="!compact">
      <el-icon><Monitor /></el-icon>
      <span>分析执行链路</span>
    </div>
    <el-timeline>
      <el-timeline-item
        v-for="step in steps"
        :key="step.id || step.name"
        :timestamp="formatDate(step.timestamp)"
        :type="getStatusType(step.status)"
        :hollow="step.status === 'pending'"
        size="large"
      >
        <div class="step-item">
          <div class="step-header">
            <span class="step-name">{{ step.name || step.step_name }}</span>
            <el-tag :type="getStatusType(step.status)" size="small" effect="plain">
              {{ step.status === 'completed' ? '完成' : step.status === 'running' ? '进行中' : step.status === 'failed' ? '失败' : '等待中' }}
            </el-tag>
          </div>
          <div class="step-detail" v-if="step.detail && !compact">
            <pre>{{ step.detail }}</pre>
          </div>
          <div class="step-meta" v-if="step.duration && !compact">
            耗时: {{ formatDuration(step.duration) }}ms
          </div>

          <!-- Expandable detail -->
          <el-button
            v-if="step.output || step.error"
            text
            size="small"
            type="primary"
            class="expand-btn"
            @click="toggleExpand(step.id || step.name)"
          >
            {{ expandedSteps.has(step.id || step.name) ? '收起详情' : '查看详情' }}
          </el-button>
          <div v-if="expandedSteps.has(step.id || step.name)" class="step-output">
            <div v-if="step.sql" class="output-section">
              <div class="output-label">SQL</div>
              <pre class="sql-pre">{{ step.sql }}</pre>
            </div>
            <div v-if="step.output" class="output-section">
              <div class="output-label">输出</div>
              <pre>{{ typeof step.output === 'string' ? step.output : JSON.stringify(step.output, null, 2) }}</pre>
            </div>
            <div v-if="step.error" class="output-section error">
              <div class="output-label">错误</div>
              <pre class="error-text">{{ step.error }}</pre>
            </div>
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Monitor } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/format'

const props = defineProps({
  steps: { type: Array, default: () => [] },
  compact: { type: Boolean, default: false },
  detailed: { type: Boolean, default: false },
})

const expandedSteps = ref(new Set())

function getStatusType(status) {
  const map = { completed: 'success', running: 'primary', failed: 'danger', pending: 'info' }
  return map[status] || 'info'
}

function formatDuration(ms) {
  if (!ms) return '-'
  if (ms < 1000) return Math.round(ms) + 'ms'
  return (ms / 1000).toFixed(2) + 's'
}

function toggleExpand(id) {
  if (expandedSteps.value.has(id)) {
    expandedSteps.value.delete(id)
  } else {
    expandedSteps.value.add(id)
  }
}
</script>

<style scoped>
.analysis-timeline {
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
}
.analysis-timeline.compact {
  padding: 8px;
  background: transparent;
}
.timeline-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}
.step-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.step-name {
  font-weight: 500;
  font-size: 14px;
}
.step-detail pre {
  font-size: 12px;
  color: #606266;
  margin: 4px 0;
  white-space: pre-wrap;
}
.step-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
.expand-btn {
  margin-top: 4px;
}
.step-output {
  margin-top: 8px;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 6px;
}
.output-section {
  margin-bottom: 8px;
}
.output-label {
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 4px;
}
.output-section pre {
  font-size: 12px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
.sql-pre {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 8px;
  border-radius: 4px;
}
.error-text {
  color: #f56c6c;
}
:deep(.el-timeline-item__timestamp) {
  font-size: 12px !important;
  color: #909399 !important;
}
</style>
