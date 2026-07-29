<template>
  <div class="datasource-page page-container">
    <div class="page-header">
      <h2>数据源管理</h2>
      <el-button type="primary" :icon="Plus" @click="openDialog()">新增数据源</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="dataSources" v-loading="loading" stripe style="width: 100%">
        <el-table-column label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tooltip :content="row.type" placement="top">
              <el-icon :size="24">
                <component :is="getTypeIcon(row.type)" />
              </el-icon>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column prop="host" label="主机" width="140" />
        <el-table-column prop="port" label="端口" width="80" />
        <el-table-column prop="database" label="数据库名" width="140" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'connected' ? 'success' : row.status === 'error' ? 'danger' : 'info'" size="small">
              {{ row.status === 'connected' ? '已连接' : row.status === 'error' ? '错误' : '未测试' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" :icon="Connection" @click="testConn(row)">测试</el-button>
            <el-button text type="primary" size="small" :icon="Edit" @click="openDialog(row)">编辑</el-button>
            <el-button text type="danger" size="small" :icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Add/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑数据源' : '新增数据源'" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="数据源名称" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="form.type" style="width: 100%">
            <el-option label="MySQL" value="mysql" />
            <el-option label="PostgreSQL" value="postgresql" />
            <el-option label="SQL Server" value="sqlserver" />
            <el-option label="Oracle" value="oracle" />
            <el-option label="MongoDB" value="mongodb" />
            <el-option label="ClickHouse" value="clickhouse" />
            <el-option label="SQLite" value="sqlite" />
          </el-select>
        </el-form-item>
        <el-form-item label="主机" prop="host">
          <el-input v-model="form.host" placeholder="localhost" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="端口" prop="port">
              <el-input-number v-model="form.port" :min="1" :max="65535" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数据库" prop="database">
              <el-input v-model="form.database" placeholder="数据库名" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="密码" />
        </el-form-item>
        <el-form-item label="额外参数">
          <el-input v-model="form.extra_params" placeholder="charset=utf8&connect_timeout=10" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Connection, Edit, Delete } from '@element-plus/icons-vue'
import {
  getDataSources, createDataSource, updateDataSource, deleteDataSource, testConnection,
} from '@/api/datasource'

const loading = ref(false)
const saving = ref(false)
const dataSources = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref(null)

const defaultForm = () => ({
  name: '', type: 'mysql', host: 'localhost', port: 3306,
  database: '', username: 'root', password: '', extra_params: '', description: '',
})

const form = reactive(defaultForm())

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  host: [{ required: true, message: '请输入主机', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口', trigger: 'blur' }],
  database: [{ required: true, message: '请输入数据库名', trigger: 'blur' }],
}

onMounted(() => loadDataSources())

async function loadDataSources() {
  loading.value = true
  try {
    const res = await getDataSources()
    dataSources.value = res.data || res.datasources || []
  } finally {
    loading.value = false
  }
}

function openDialog(row) {
  if (row) {
    isEdit.value = true
    editId.value = row.id
    Object.assign(form, row)
  } else {
    isEdit.value = false
    editId.value = null
    Object.assign(form, defaultForm())
  }
  dialogVisible.value = true
}

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (isEdit.value) {
      await updateDataSource(editId.value, form)
      ElMessage.success('更新成功')
    } else {
      await createDataSource(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await loadDataSources()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除数据源 "${row.name}"？`, '提示', { type: 'warning' })
    await deleteDataSource(row.id)
    ElMessage.success('已删除')
    await loadDataSources()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

async function testConn(row) {
  try {
    await testConnection(row.id)
    ElMessage.success('连接成功')
    await loadDataSources()
  } catch {
    await loadDataSources()
  }
}

function getTypeIcon(type) {
  const icons = {
    mysql: 'Coin', postgresql: 'Coin', sqlserver: 'Coin',
    oracle: 'Coin', mongodb: 'Coin', clickhouse: 'Coin', sqlite: 'Coin',
  }
  return icons[type] || 'Coin'
}
</script>
