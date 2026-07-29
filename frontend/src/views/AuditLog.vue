<template>
  <div class="audit-log-page page-container">
    <div class="page-header">
      <h2>审计日志</h2>
      <el-button :icon="Refresh" @click="loadLogs">刷新</el-button>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="filters" size="small">
        <el-form-item label="操作类型">
          <el-select v-model="filters.action" clearable placeholder="全部操作" style="width: 150px">
            <el-option label="登录" value="login" />
            <el-option label="登出" value="logout" />
            <el-option label="查询数据" value="query" />
            <el-option label="创建数据源" value="create_datasource" />
            <el-option label="删除数据源" value="delete_datasource" />
            <el-option label="上传文档" value="upload_doc" />
            <el-option label="删除文档" value="delete_doc" />
            <el-option label="生成报表" value="generate_report" />
            <el-option label="用户管理" value="user_manage" />
            <el-option label="系统设置" value="system_setting" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作用户">
          <el-input v-model="filters.username" placeholder="用户名" style="width: 140px" />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadLogs">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="logs" v-loading="loading" stripe style="width: 100%">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column label="操作类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.action_name || row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="操作用户" width="130" />
        <el-table-column prop="ip_address" label="IP地址" width="140" />
        <el-table-column prop="detail" label="操作详情" min-width="300" show-overflow-tooltip />
        <el-table-column prop="created_at" label="操作时间" width="170" :formatter="(r) => formatDate(r.created_at)" />
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" :icon="View" @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-pagination
      v-if="total > 0"
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      background
      style="margin-top: 16px; justify-content: flex-end"
      @change="loadLogs"
    />

    <!-- Detail Dialog -->
    <el-dialog v-model="detailVisible" title="日志详情" width="600px">
      <template v-if="currentLog">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="操作ID">{{ currentLog.id }}</el-descriptions-item>
          <el-descriptions-item label="操作类型">{{ currentLog.action_name || currentLog.action }}</el-descriptions-item>
          <el-descriptions-item label="操作用户">{{ currentLog.username }}</el-descriptions-item>
          <el-descriptions-item label="IP地址">{{ currentLog.ip_address }}</el-descriptions-item>
          <el-descriptions-item label="User-Agent">{{ currentLog.user_agent || '-' }}</el-descriptions-item>
          <el-descriptions-item label="操作时间">{{ formatDate(currentLog.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="操作详情">{{ currentLog.detail }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="currentLog.request_data" style="margin-top: 12px">
          <h4 style="font-size:14px;margin:0 0 8px">请求数据</h4>
          <pre style="background:#f5f7fa;padding:12px;border-radius:6px;font-size:13px;max-height:200px;overflow:auto">{{ JSON.stringify(currentLog.request_data, null, 2) }}</pre>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Refresh, View } from '@element-plus/icons-vue'
import request from '@/api/request'
import { formatDate } from '@/utils/format'

const loading = ref(false)
const logs = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const detailVisible = ref(false)
const currentLog = ref(null)

const filters = reactive({
  action: '', username: '', dateRange: null,
})

onMounted(() => loadLogs())

async function loadLogs() {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      action: filters.action || undefined,
      username: filters.username || undefined,
      start_time: filters.dateRange?.[0]?.toISOString(),
      end_time: filters.dateRange?.[1]?.toISOString(),
    }
    const res = await request.get('/admin/logs', { params })
    logs.value = res.data || res.logs || []
    total.value = res.total || res.count || 0
  } finally {
    loading.value = false
  }
}

function viewDetail(row) {
  currentLog.value = row
  detailVisible.value = true
}
</script>

<style scoped>
.filter-card {
  margin-bottom: 16px;
}
</style>
