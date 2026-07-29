<template>
  <div class="settings-page page-container">
    <div class="page-header">
      <h2>系统设置</h2>
      <el-button type="primary" :loading="saving" @click="handleSave">保存设置</el-button>
    </div>

    <el-card shadow="never">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="通用设置" name="general">
          <el-form label-width="120px" style="max-width: 600px">
            <el-form-item label="系统名称">
              <el-input v-model="settings.system_name" placeholder="DataAnalysis Agent" />
            </el-form-item>
            <el-form-item label="系统语言">
              <el-select v-model="settings.language" style="width: 100%">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
            <el-form-item label="每页条数">
              <el-input-number v-model="settings.page_size" :min="10" :max="100" />
            </el-form-item>
            <el-form-item label="会话超时(分钟)">
              <el-input-number v-model="settings.session_timeout" :min="5" :max="1440" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="模型配置" name="model">
          <el-form label-width="140px" style="max-width: 600px">
            <el-form-item label="LLM模型">
              <el-select v-model="settings.llm_model" style="width: 100%">
                <el-option label="GPT-4o" value="gpt-4o" />
                <el-option label="GPT-4o-mini" value="gpt-4o-mini" />
                <el-option label="GPT-4" value="gpt-4" />
                <el-option label="Claude 3.5 Sonnet" value="claude-3.5-sonnet" />
                <el-option label="通义千问" value="qwen" />
              </el-select>
            </el-form-item>
            <el-form-item label="API Key">
              <el-input v-model="settings.api_key" type="password" show-password placeholder="输入 API Key" />
            </el-form-item>
            <el-form-item label="API Base URL">
              <el-input v-model="settings.api_base_url" placeholder="https://api.openai.com/v1" />
            </el-form-item>
            <el-form-item label="温度">
              <el-slider v-model="settings.temperature" :min="0" :max="2" :step="0.1" show-input style="width: 300px" />
            </el-form-item>
            <el-form-item label="最大Token数">
              <el-input-number v-model="settings.max_tokens" :min="256" :max="32768" :step="256" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="Agent配置" name="agent">
          <el-form label-width="140px" style="max-width: 600px">
            <el-form-item label="最大执行步骤">
              <el-input-number v-model="settings.max_steps" :min="1" :max="20" />
            </el-form-item>
            <el-form-item label="SQL超时(秒)">
              <el-input-number v-model="settings.sql_timeout" :min="10" :max="300" />
            </el-form-item>
            <el-form-item label="启用知识库">
              <el-switch v-model="settings.enable_knowledge" />
            </el-form-item>
            <el-form-item label="查询结果条数">
              <el-input-number v-model="settings.max_results" :min="10" :max="10000" :step="10" />
            </el-form-item>
            <el-form-item label="自动可视化">
              <el-switch v-model="settings.auto_visualize" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="通知设置" name="notify">
          <el-form label-width="140px" style="max-width: 600px">
            <el-form-item label="任务完成通知">
              <el-switch v-model="settings.notify_on_complete" />
            </el-form-item>
            <el-form-item label="任务失败通知">
              <el-switch v-model="settings.notify_on_error" />
            </el-form-item>
            <el-form-item label="通知邮箱">
              <el-input v-model="settings.notify_email" placeholder="admin@example.com" />
            </el-form-item>
            <el-form-item label="Webhook URL">
              <el-input v-model="settings.webhook_url" placeholder="https://hooks.example.com/alert" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const activeTab = ref('general')
const saving = ref(false)

const settings = reactive({
  system_name: 'DataAnalysis Agent',
  language: 'zh-CN',
  page_size: 20,
  session_timeout: 30,
  llm_model: 'gpt-4o',
  api_key: '',
  api_base_url: '',
  temperature: 0.3,
  max_tokens: 4096,
  max_steps: 10,
  sql_timeout: 60,
  enable_knowledge: true,
  max_results: 100,
  auto_visualize: true,
  notify_on_complete: false,
  notify_on_error: true,
  notify_email: '',
  webhook_url: '',
})

onMounted(async () => {
  try {
    const res = await request.get('/admin/settings')
    const data = res.data || res.settings || {}
    Object.assign(settings, data)
  } catch {
    // Use defaults
  }
})

async function handleSave() {
  saving.value = true
  try {
    await request.put('/admin/settings', settings)
    ElMessage.success('设置已保存')
  } finally {
    saving.value = false
  }
}
</script>
