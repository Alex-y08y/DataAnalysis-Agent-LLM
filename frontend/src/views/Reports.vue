<template>
  <div class="reports-page page-container">
    <div class="page-header">
      <h2>报表中心</h2>
      <el-button type="primary" :icon="Plus" @click="openGenerateDialog">生成报表</el-button>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="报表列表" name="reports">
        <el-card shadow="never">
          <el-table :data="reports" v-loading="loading" stripe style="width: 100%">
            <el-table-column prop="title" label="报表标题" min-width="180" />
            <el-table-column label="类型" prop="type" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.type === 'daily' ? '日报' : row.type === 'weekly' ? '周报' : row.type === 'monthly' ? '月报' : '自定义' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'generating' ? 'warning' : 'info'" size="small">
                  {{ row.status === 'completed' ? '已完成' : row.status === 'generating' ? '生成中' : '待生成' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="170" :formatter="(r) => formatDate(r.created_at)" />
            <el-table-column label="操作" width="240" fixed="right">
              <template #default="{ row }">
                <el-button text type="primary" size="small" :icon="View" @click="previewReport(row)">预览</el-button>
                <el-button text type="primary" size="small" :icon="Download" @click="handleExport(row, 'pdf')">导出PDF</el-button>
                <el-button text type="primary" size="small" :icon="Download" @click="handleExport(row, 'excel')">导出Excel</el-button>
                <el-button text type="danger" size="small" :icon="Delete" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="定时任务" name="schedules">
        <el-card shadow="never">
          <el-button type="primary" :icon="Plus" size="small" style="margin-bottom: 16px" @click="showScheduleDialog = true">新增定时任务</el-button>
          <el-table :data="schedules" stripe style="width: 100%">
            <el-table-column prop="name" label="任务名称" min-width="150" />
            <el-table-column prop="cron" label="Cron表达式" width="140" />
            <el-table-column prop="report_type" label="报表类型" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.report_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-switch v-model="row.enabled" @change="toggleSchedule(row)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button text type="danger" size="small" :icon="Delete" @click="handleDeleteSchedule(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- Generate Report Dialog -->
    <el-dialog v-model="generateVisible" title="生成报表" width="500px">
      <el-form label-width="100px">
        <el-form-item label="报表标题">
          <el-input v-model="reportForm.title" placeholder="输入报表标题" />
        </el-form-item>
        <el-form-item label="报表类型">
          <el-select v-model="reportForm.type" style="width: 100%">
            <el-option label="日报" value="daily" />
            <el-option label="周报" value="weekly" />
            <el-option label="月报" value="monthly" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据源">
          <el-select v-model="reportForm.datasource_id" style="width: 100%" filterable>
            <el-option v-for="ds in dataSources" :key="ds.id" :label="ds.name" :value="ds.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="分析需求">
          <el-input v-model="reportForm.description" type="textarea" :rows="4" placeholder="描述报表分析需求和关注指标..." />
        </el-form-item>
        <el-form-item label="图表类型">
          <el-checkbox-group v-model="reportForm.chart_types">
            <el-checkbox label="line">折线图</el-checkbox>
            <el-checkbox label="bar">柱状图</el-checkbox>
            <el-checkbox label="pie">饼图</el-checkbox>
            <el-checkbox label="table">数据表</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="generateVisible = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="handleGenerate">立即生成</el-button>
      </template>
    </el-dialog>

    <!-- Preview Dialog -->
    <el-dialog v-model="previewVisible" title="报表预览" width="80%" top="5vh">
      <div v-if="previewData" class="report-preview">
        <h2>{{ previewData.title }}</h2>
        <p class="report-date">{{ formatDate(previewData.created_at) }}</p>
        <div class="report-content" v-html="previewData.content_html"></div>
      </div>
    </el-dialog>

    <!-- Schedule Dialog -->
    <el-dialog v-model="showScheduleDialog" title="新增定时任务" width="480px">
      <el-form label-width="110px">
        <el-form-item label="任务名称">
          <el-input v-model="scheduleForm.name" placeholder="定时任务名称" />
        </el-form-item>
        <el-form-item label="报表类型">
          <el-select v-model="scheduleForm.report_type" style="width: 100%">
            <el-option label="日报" value="daily" />
            <el-option label="周报" value="weekly" />
            <el-option label="月报" value="monthly" />
          </el-select>
        </el-form-item>
        <el-form-item label="Cron表达式">
          <el-input v-model="scheduleForm.cron" placeholder="0 8 * * *" />
          <div style="font-size:12px;color:#909399;margin-top:4px">格式: 分 时 日 月 周</div>
        </el-form-item>
        <el-form-item label="数据源">
          <el-select v-model="scheduleForm.datasource_id" style="width: 100%" filterable>
            <el-option v-for="ds in dataSources" :key="ds.id" :label="ds.name" :value="ds.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showScheduleDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingSchedule" @click="handleSaveSchedule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, View, Download, Delete } from '@element-plus/icons-vue'
import { getReports, createReport, deleteReport, exportReport, createSchedule, getSchedules, deleteSchedule } from '@/api/report'
import { getDataSources } from '@/api/datasource'
import { formatDate } from '@/utils/format'

const activeTab = ref('reports')
const loading = ref(false)
const reports = ref([])
const schedules = ref([])
const dataSources = ref([])
const generateVisible = ref(false)
const generating = ref(false)
const previewVisible = ref(false)
const previewData = ref(null)
const showScheduleDialog = ref(false)
const savingSchedule = ref(false)

const reportForm = ref({
  title: '', type: 'daily', datasource_id: null, description: '', chart_types: ['line', 'bar'],
})

const scheduleForm = ref({
  name: '', report_type: 'daily', cron: '0 8 * * *', datasource_id: null,
})

onMounted(async () => {
  await Promise.all([loadReports(), loadSchedules(), loadDataSources()])
})

async function loadReports() {
  loading.value = true
  try {
    const res = await getReports()
    reports.value = res.data || res.reports || []
  } finally {
    loading.value = false
  }
}

async function loadSchedules() {
  try {
    const res = await getSchedules()
    schedules.value = res.data || res.schedules || []
  } catch { /* ignore */ }
}

async function loadDataSources() {
  try {
    const res = await getDataSources()
    dataSources.value = res.data || res.datasources || []
  } catch { /* ignore */ }
}

function openGenerateDialog() {
  reportForm.value = { title: '', type: 'daily', datasource_id: null, description: '', chart_types: ['line', 'bar'] }
  generateVisible.value = true
}

async function handleGenerate() {
  if (!reportForm.value.title || !reportForm.value.description) {
    ElMessage.warning('请填写标题和分析需求')
    return
  }
  generating.value = true
  try {
    await createReport(reportForm.value)
    ElMessage.success('报表已开始生成')
    generateVisible.value = false
    await loadReports()
  } finally {
    generating.value = false
  }
}

function previewReport(row) {
  previewData.value = row
  previewVisible.value = true
}

async function handleExport(row, format) {
  try {
    const res = await exportReport(row.id, format)
    const url = window.URL.createObjectURL(new Blob([res]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${row.title}.${format}`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除报表 "${row.title}"？`, '提示', { type: 'warning' })
    await deleteReport(row.id)
    ElMessage.success('已删除')
    await loadReports()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

async function handleSaveSchedule() {
  savingSchedule.value = true
  try {
    await createSchedule(scheduleForm.value)
    ElMessage.success('定时任务已创建')
    showScheduleDialog.value = false
    await loadSchedules()
  } finally {
    savingSchedule.value = false
  }
}

async function handleDeleteSchedule(row) {
  try {
    await ElMessageBox.confirm(`确定删除定时任务 "${row.name}"？`, '提示', { type: 'warning' })
    await deleteSchedule(row.id)
    ElMessage.success('已删除')
    await loadSchedules()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

function toggleSchedule(row) {
  // Placeholder for schedule toggle
  ElMessage.success(row.enabled ? '已启用' : '已禁用')
}
</script>

<style scoped>
.report-preview {
  padding: 24px;
}
.report-preview h2 {
  margin: 0 0 8px;
}
.report-date {
  color: #909399;
  font-size: 13px;
  margin-bottom: 24px;
}
.report-content {
  line-height: 1.8;
}
:deep(.report-content table) {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}
:deep(.report-content th, .report-content td) {
  border: 1px solid #e4e7ed;
  padding: 8px 12px;
  text-align: left;
}
:deep(.report-content th) {
  background: #f5f7fa;
}
</style>
