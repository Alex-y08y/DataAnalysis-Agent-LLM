<template>
  <div class="knowledge-page page-container">
    <div class="page-header">
      <h2>知识库管理</h2>
      <div>
        <el-button @click="loadDocs" :icon="Refresh">刷新</el-button>
        <el-button type="primary" :icon="Upload" @click="uploadVisible = true">上传文档</el-button>
      </div>
    </div>

    <el-card shadow="never" class="search-card">
      <el-input v-model="searchQuery" placeholder="搜索知识库文档..." :prefix-icon="Search" clearable @input="handleSearch" />
    </el-card>

    <el-card shadow="never">
      <el-table :data="documents" v-loading="loading" stripe style="width: 100%">
        <el-table-column label="文件名" prop="filename" min-width="200">
          <template #default="{ row }">
            <div class="file-info">
              <el-icon :size="20" :color="getFileColor(row.file_type)"><Document /></el-icon>
              <span class="filename">{{ row.filename }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="类型" prop="file_type" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.file_type?.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="标签" width="200">
          <template #default="{ row }">
            <el-tag v-for="tag in (row.tags || [])" :key="tag" size="small" style="margin-right: 4px">{{ tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" prop="file_size" width="100" :formatter="(r) => formatFileSize(r.file_size)" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'indexed' ? 'success' : row.status === 'indexing' ? 'warning' : 'info'" size="small">
              {{ row.status === 'indexed' ? '已索引' : row.status === 'indexing' ? '索引中' : '待索引' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="上传时间" prop="created_at" width="170" :formatter="(r) => formatDate(r.created_at)" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status !== 'indexing'" text type="primary" size="small" :icon="Refresh" @click="handleRebuild(row)">重建索引</el-button>
            <el-button text type="danger" size="small" :icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Upload Dialog -->
    <el-dialog v-model="uploadVisible" title="上传知识文档" width="500px">
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".pdf,.doc,.docx,.txt,.md,.csv,.xlsx,.xls"
      >
        <el-icon :size="48" color="#c0c4cc"><UploadFilled /></el-icon>
        <div class="upload-text">
          <span>拖拽文件到此处，或 <em>点击选择文件</em></span>
        </div>
        <template #tip>
          <div class="upload-tip">支持 PDF、Word、TXT、Markdown、CSV、Excel 格式</div>
        </template>
      </el-upload>
      <el-form label-width="80px" style="margin-top: 16px">
        <el-form-item label="文档类型">
          <el-select v-model="uploadForm.doc_type" style="width: 100%">
            <el-option label="业务文档" value="business" />
            <el-option label="技术文档" value="technical" />
            <el-option label="数据字典" value="dictionary" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="uploadForm.tags" multiple allow-create filterable default-first-option style="width: 100%">
            <el-option label="销售" value="销售" />
            <el-option label="财务" value="财务" />
            <el-option label="用户" value="用户" />
            <el-option label="产品" value="产品" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="2" placeholder="文档描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Upload, Search, Delete, Document, UploadFilled } from '@element-plus/icons-vue'
import { getKnowledgeDocs, uploadKnowledgeDoc, deleteKnowledgeDoc, rebuildIndex } from '@/api/knowledge'
import { formatDate, formatFileSize } from '@/utils/format'

const loading = ref(false)
const documents = ref([])
const searchQuery = ref('')
const uploadVisible = ref(false)
const uploading = ref(false)
const uploadRef = ref(null)
const selectedFile = ref(null)

const uploadForm = ref({
  doc_type: 'business',
  tags: [],
  description: '',
})

onMounted(() => loadDocs())

async function loadDocs() {
  loading.value = true
  try {
    const res = await getKnowledgeDocs({ search: searchQuery.value })
    documents.value = res.data || res.documents || []
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  loadDocs()
}

function handleFileChange(file) {
  selectedFile.value = file.raw
}

async function handleUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('doc_type', uploadForm.value.doc_type)
    formData.append('tags', JSON.stringify(uploadForm.value.tags))
    formData.append('description', uploadForm.value.description)
    await uploadKnowledgeDoc(formData)
    ElMessage.success('上传成功')
    uploadVisible.value = false
    uploadForm.value = { doc_type: 'business', tags: [], description: '' }
    selectedFile.value = null
    await loadDocs()
  } catch {
    // Error handled by interceptor
  } finally {
    uploading.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除 "${row.filename}"？`, '提示', { type: 'warning' })
    await deleteKnowledgeDoc(row.id)
    ElMessage.success('已删除')
    await loadDocs()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

async function handleRebuild(row) {
  try {
    await rebuildIndex(row.id)
    ElMessage.success('已触发索引重建')
    await loadDocs()
  } catch {
    // Error handled by interceptor
  }
}

function getFileColor(type) {
  const colors = { pdf: '#f56c6c', doc: '#409eff', docx: '#409eff', txt: '#67c23a', md: '#909399', csv: '#e6a23c', xlsx: '#67c23a' }
  return colors[type] || '#909399'
}
</script>

<style scoped>
.search-card {
  margin-bottom: 16px;
}
.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.filename {
  font-weight: 500;
}
.upload-text em {
  color: #409eff;
  font-style: normal;
}
.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}
</style>
