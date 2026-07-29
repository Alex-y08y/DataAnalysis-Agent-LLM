<template>
  <div class="tasks-page page-container">
    <div class="page-header">
      <h2>任务管理</h2>
      <el-button :icon="Refresh" @click="loadTasks">刷新</el-button>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="filters" size="small">
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部状态" style="width: 120px">
            <el-option label="运行中" value="running" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.type" clearable placeholder="全部类型" style="width: 120px">
            <el-option label="数据分析" value="analysis" />
            <el-option label="报表生成" value="report" />
            <el-option label="数据导入" value="import" />
            <el-option label="索引重建" value="rebuild" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTasks">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="tasks" v-loading="loading" stripe style="width: 100%">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="task_name" label="任务名称" min-width="180" />
        <el-table-column label="类型" width="110">
          <template #default="{ row }">
            <el-tag size="small">{{ row.type === 'analysis' ? '数据分析' : row.type === 'report' ? '报表生成' : row.type === 'import' ? '数据导入' : row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : row.status === 'running' ? 'warning' : row.status === 'failed' ? 'danger' : 'info'" size="small">
              {{ row.status === 'success' ? '成功' : row.status === 'running' ? '运行中' : row.status === 'failed' ? '失败' : '已取消' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="160">
          <template #default="{ row }">
            <el-progress :percentage="row.progress || 0" :status="row.status === 'failed' ? 'exception' : undefined" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" :formatter="(r) => formatDate(r.created_at)" />
        <el-table-column prop="duration" label="耗时" width="100" :formatter="(r) => r.duration ? formatDuration(r.duration) : '-'" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" :icon="View" @click="viewDetail(row)">详情</el-button>
            <el-button text type="primary" size="small" :icon="CopyDocument" @click="reuseTask(row)">复用</el-button>
            <el-button v-if="row.status === 'running'" text type="danger" size="small" :icon="Close" @click="cancelTask(row)">取消</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Detail Dialog -->
    <el-dialog v-model="detailVisible" title="任务详情" width="700px">
      <template v-if="currentTask">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务名称">{{ currentTask.task_name }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ currentTask.type }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentTask.status === 'success' ? 'success' : 'danger'" size="small">
              {{ currentTask.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="进度">{{ currentTask.progress }}%</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(currentTask.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="耗时">{{ currentTask.duration ? formatDuration(currentTask.duration) : '-' }}</el-descriptions-item>
          <el-descriptions-item label="执行人">{{ currentTask.user_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="数据源">{{ currentTask.datasource_name || '-' }}</el-descriptions-item>
        </el-descriptions>
        <div class="task-result" v-if="currentTask.result">
          <h4>执行结果</h4>
          <pre>{{ currentTask.result }}</pre>
        </div>
        <div class="task-error" v-if="currentTask.error_message">
          <h4>错误信息</h4>
          <pre class="error-text">{{ currentTask.error_message }}</pre>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, View, CopyDocument, Close } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { formatDate } from '@/utils/format'

const router = useRouter()
const loading = ref(false)
const tasks = ref([])
const detailVisible = ref(false)
const currentTask = ref(null)

// Placeholder — replace with actual API import when backend is ready
const filters = reactive({
  status: '', type: '', dateRange: null,
})

onMounted(() => loadTasks())

async function loadTasks() {
  loading.value = true
  try {
    // Replace with actual API call
    tasks.value = []
    loading.value = false
  } catch {
    loading.value = false
  }
}

function viewDetail(row) {
  currentTask.value = row
  detailVisible.value = true
}

function reuseTask(row) {
  router.push('/')
  ElMessage.success('已复制任务参数')
}

async function cancelTask(row) {
  try {
    await ElMessageBox.confirm('确定取消此任务？', '提示', { type: 'warning' })
    ElMessage.success('已取消')
    await loadTasks()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

function formatDuration(seconds) {
  if (!seconds) return '-'
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
  return `${Math.floor(seconds / 3600)}时${Math.floor((seconds % 3600) / 60)}分`
}
</script>

<style scoped>
.filter-card {
  margin-bottom: 16px;
}
.task-result, .task-error {
  margin-top: 16px;
}
.task-result h4, .task-error h4 {
  margin: 0 0 8px;
  font-size: 14px;
}
.task-result pre, .task-error pre {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  font-size: 13px;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
}
.error-text {
  color: #f56c6c;
}
</style>
