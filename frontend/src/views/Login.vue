<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <el-icon :size="48" color="#409eff"><DataAnalysis /></el-icon>
        <h2>DataAnalysis Agent</h2>
        <p class="subtitle">智能数据分析平台</p>
      </div>
      <el-card shadow="never" class="login-card">
        <el-tabs v-model="activeTab" class="login-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" size="large" @keyup.enter="handleLogin">
              <el-form-item prop="username">
                <el-input v-model="loginForm.username" placeholder="用户名" :prefix-icon="User" />
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="loginForm.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" size="large" style="width: 100%" :loading="loading" @click="handleLogin">
                  登 录
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="注册" name="register">
            <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" size="large" @keyup.enter="handleRegister">
              <el-form-item prop="username">
                <el-input v-model="registerForm.username" placeholder="用户名" :prefix-icon="User" />
              </el-form-item>
              <el-form-item prop="email">
                <el-input v-model="registerForm.email" placeholder="邮箱" :prefix-icon="Message" />
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="registerForm.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password />
              </el-form-item>
              <el-form-item prop="confirmPassword">
                <el-input v-model="registerForm.confirmPassword" type="password" placeholder="确认密码" :prefix-icon="Lock" show-password />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" size="large" style="width: 100%" :loading="loading" @click="handleRegister">
                  注 册
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, DataAnalysis } from '@element-plus/icons-vue'
import { useUserStore } from '@/store'
import { register } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('login')
const loading = ref(false)
const loginFormRef = ref(null)
const registerFormRef = ref(null)

const loginForm = reactive({
  username: '',
  password: '',
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const registerRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [{ required: true, type: 'email', message: '请输入有效邮箱', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少6位', trigger: 'blur' }],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: (rule, value, callback) => {
      if (value !== registerForm.password) callback(new Error('两次密码不一致'))
      else callback()
    }, trigger: 'blur' },
  ],
}

async function handleLogin() {
  const valid = await loginFormRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await userStore.loginAction(loginForm)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  const valid = await registerFormRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await register(registerForm)
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
    loginForm.username = registerForm.username
  } catch (e) {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-container {
  width: 420px;
}
.login-header {
  text-align: center;
  color: #fff;
  margin-bottom: 24px;
}
.login-header h2 {
  margin: 12px 0 4px;
  font-size: 28px;
  font-weight: 600;
}
.subtitle {
  font-size: 14px;
  opacity: 0.8;
  margin: 0;
}
.login-card {
  border-radius: 12px;
}
.login-tabs {
  padding: 8px 0;
}
</style>
