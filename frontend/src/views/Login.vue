<!-- frontend/src/views/Login.vue (保留原UI：两步式登录，修复 Hash 跳转) -->
<template>
  <div class="login-page">
    <div class="logo-area" @click="handleSecretClick">
      <h1>XX零工市场</h1>
      <p>同城好工作 · 就在零工市场</p>
    </div>

    <div v-if="currentStep === 1" class="step-container fade-in">
      <div class="main-btns">
        <button class="btn-main" @click="selectRole('worker')">求职者登录</button>
        <button class="btn-sub" @click="selectRole('merchant')">招聘方登录</button>
        <button class="btn-sub" @click="selectRole('provider')">本地生活服务商登录</button>
      </div>
    </div>

    <div v-if="currentStep === 2" class="step-container fade-in">
      <div class="back-header">
        <span class="btn-back" @click="goBack">← 返回</span>
        <span class="current-role">{{ roleNameMap[selectedRole] }}</span>
        <span class="placeholder-right"></span>
      </div>
      <div class="input-group">
        <input type="tel" v-model="phone" placeholder="请输入您的手机号" maxlength="11" autofocus />
      </div>
      <button class="btn-main" @click="handleLogin" :disabled="loading">
        {{ loading ? '正在登录...' : '确认登录' }}
      </button>
      <p class="tips">未注册的手机号验证后将自动创建账号</p>
    </div>

    <div class="bottom-roles" v-if="showAdminEntries">
      <span @click="goToAdmin('agent')">经纪人</span> |
      <span @click="goToAdmin('ops')">运营方</span> |
      <span @click="goToAdmin('gov')">监管方</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api'
import { useUserStore } from '../store/user'

const userStore = useUserStore()
const currentStep = ref(1)
const selectedRole = ref('')
const phone = ref('')
const loading = ref(false)

const roleNameMap = { worker: '求职者登录', merchant: '招聘方登录', provider: '服务商登录' }

const clickCount = ref(0)
const showAdminEntries = ref(false)
let clickTimer = null

const handleSecretClick = () => {
  if (showAdminEntries.value) return
  clickCount.value++
  if (clickTimer) clearTimeout(clickTimer)
  clickTimer = setTimeout(() => { clickCount.value = 0 }, 1000)
  if (clickCount.value >= 5) {
    showAdminEntries.value = true
    window.$toast('内部管理入口已解锁')
    clickCount.value = 0
    clearTimeout(clickTimer)
  }
}

const selectRole = (role) => {
  selectedRole.value = role
  phone.value = ''
  currentStep.value = 2
}

const goBack = () => {
  currentStep.value = 1
  selectedRole.value = ''
}

const handleLogin = async () => {
  if (!phone.value || phone.value.length < 11) return window.$toast('请输入正确的 11 位手机号')
  loading.value = true
  try {
    const res = await api.post('/auth/login', { phone: phone.value, target_role: selectedRole.value })
    userStore.setLogin(res.data, selectedRole.value)
    window.$toast('登录成功')

    setTimeout(() => {
      // 🚨 修复：使用 Hash 模式跳转
      if (selectedRole.value === 'worker') {
        window.location.hash = '#/worker/home'
      } else if (selectedRole.value === 'merchant') {
        window.location.hash = '#/merchant/dash'
      } else if (selectedRole.value === 'provider') {
        window.$toast('服务商工作台正在开发中，为您跳转至商家端')
        window.location.hash = '#/merchant/dash'
      }
    }, 500)
  } catch (err) {
    window.$toast(err.response?.data?.detail || '登录失败，请检查网络')
  } finally {
    loading.value = false
  }
}

const goToAdmin = (role) => {
  localStorage.setItem('token', 'admin-mock-token-xyz')
  localStorage.setItem('activeRole', role)

  // 🚨 修复：使用 Hash 模式跳转
  if (role === 'ops') {
    window.$toast('正在进入平台运营后台...')
    setTimeout(() => { window.location.hash = '#/admin/dash' }, 800)
  } else if (role === 'gov') {
    window.$toast('正在进入合规监管后台...')
    setTimeout(() => { window.location.hash = '#/admin/dash' }, 800)
  } else if (role === 'agent') {
    window.$toast('正在跳转至经纪人资质审核...')
    setTimeout(() => { window.location.hash = '#/admin/audit' }, 800)
  }
}
</script>

<style scoped>
/* 保留原有样式不变 */
.login-page { min-height: 100vh; padding: 80px 30px; background: #fff; display: flex; flex-direction: column; }
.logo-area { text-align: center; margin-bottom: 40px; cursor: pointer; user-select: none; }
.logo-area h1 { font-size: 28px; color: #2563eb; font-weight: bold; margin-bottom: 10px; }
.logo-area p { color: #6b7280; font-size: 14px; }
.step-container { display: flex; flex-direction: column; flex: 1; }
.fade-in { animation: fadeIn 0.3s ease-in-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.back-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; font-size: 16px; font-weight: bold; color: #1f2937; }
.btn-back { color: #6b7280; font-size: 14px; font-weight: normal; cursor: pointer; }
.placeholder-right { width: 40px; }
.input-group { margin-bottom: 30px; }
.input-group input { width: 100%; padding: 16px; font-size: 18px; border: 1px solid #e5e7eb; border-radius: 8px; background: #f9fafb; outline: none; text-align: center; letter-spacing: 2px; font-weight: bold; color: #333; }
.input-group input:focus { border-color: #2563eb; background: #fff; }
.main-btns { display: flex; flex-direction: column; gap: 16px; }
.btn-main { padding: 16px; background: #2563eb; color: #fff; border-radius: 8px; font-size: 18px; font-weight: bold; border: none; cursor: pointer; }
.btn-main:disabled { opacity: 0.7; }
.btn-sub { padding: 16px; background: #eff6ff; color: #2563eb; border: 1px solid #2563eb; border-radius: 8px; font-size: 18px; font-weight: bold; cursor: pointer; }
.tips { text-align: center; font-size: 13px; color: #9ca3af; margin-top: 16px; }
.bottom-roles { margin-top: auto; text-align: center; padding-bottom: 20px; color: #6b7280; font-size: 14px; }
.bottom-roles span { cursor: pointer; margin: 0 8px; }
.bottom-roles span:active { color: #2563eb; }
</style>