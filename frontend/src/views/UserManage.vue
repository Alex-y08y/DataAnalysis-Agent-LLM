<template>
  <div class="user-manage-page page-container">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">新增用户</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="users" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" min-width="140" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-select :model-value="row.role" size="small" @change="(val) => handleRoleChange(row, val)">
              <el-option label="管理员" value="admin" />
              <el-option label="普通用户" value="user" />
              <el-option label="只读用户" value="readonly" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" @change="(val) => handleToggleActive(row, val)" />
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="170" :formatter="(r) => formatDate(r.last_login)" />
        <el-table-column prop="created_at" label="创建时间" width="170" :formatter="(r) => formatDate(r.created_at)" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" :icon="Edit" @click="editUser(row)">编辑</el-button>
            <el-button text type="danger" size="small" :icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新增用户'" width="450px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
            <el-option label="只读用户" value="readonly" />
          </el-select>
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
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import request from '@/api/request'
import { formatDate } from '@/utils/format'

const loading = ref(false)
const saving = ref(false)
const users = ref([])
const dialogVisible = ref(false)
const showCreateDialog = ref(false)
const isEdit = ref(false)
const editUserId = ref(null)
const formRef = ref(null)

const form = reactive({
  username: '', email: '', password: '', role: 'user',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [{ required: true, type: 'email', message: '请输入有效邮箱', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少6位', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

onMounted(() => loadUsers())

async function loadUsers() {
  loading.value = true
  try {
    const res = await request.get('/admin/users')
    users.value = res.data || res.users || []
  } finally {
    loading.value = false
  }
}

function editUser(row) {
  isEdit.value = true
  editUserId.value = row.id
  form.username = row.username
  form.email = row.email
  form.role = row.role
  form.password = ''
  dialogVisible.value = true
}

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (isEdit.value) {
      await request.put(`/admin/users/${editUserId.value}`, form)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/users', form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await loadUsers()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除用户 "${row.username}"？`, '提示', { type: 'warning' })
    await request.delete(`/admin/users/${row.id}`)
    ElMessage.success('已删除')
    await loadUsers()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

async function handleRoleChange(row, role) {
  try {
    await request.put(`/admin/users/${row.id}`, { role })
    ElMessage.success('角色已更新')
  } catch {
    await loadUsers()
  }
}

async function handleToggleActive(row, val) {
  try {
    await request.put(`/admin/users/${row.id}`, { is_active: val })
    ElMessage.success(val ? '已启用' : '已禁用')
  } catch {
    await loadUsers()
  }
}

// Sync dialog visibility with create button
import { watch } from 'vue'
watch(showCreateDialog, (val) => {
  if (val) {
    isEdit.value = false
    editUserId.value = null
    form.username = ''
    form.email = ''
    form.password = ''
    form.role = 'user'
    dialogVisible.value = true
    showCreateDialog.value = false
  }
})
</script>
