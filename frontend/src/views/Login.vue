<!-- frontend/src/views/Login.vue —— 登录（选角色保留 + 意图驱动直通）
     1) 普通进入：显示「求职者 / 招聘方 / 服务商」角色选择，照顾新用户
     2) 带意图进入：?role=merchant 时跳过选角色，直接进该角色的手机号登录
        C 端投递  -> /#/login?role=worker&redirect=/worker/job-detail/5
        商家发岗  -> /#/login?role=merchant&redirect=/merchant/dash
-->
<template>
  <div class="login-page">
    <div class="logo-area" @click="handleSecretClick">
      <h1>XX零工市场</h1>
      <p>同城好工作 · 就在零工市场</p>
    </div>

    <!-- 第一步：选择身份（意图直通时自动跳过） -->
    <div v-if="currentStep === 1" class="step-container fade-in">
      <p class="step-hint">请选择您的身份</p>
      <div class="main-btns">
        <button class="btn-main" @click="selectRole('worker')">求职者登录</button>
        <button class="btn-sub" @click="selectRole('merchant')">招聘方登录</button>
        <button class="btn-sub" @click="selectRole('provider')">本地生活服务商登录</button>
      </div>
      <p class="tips">登录即代表同意《用户协议》《隐私政策》</p>
    </div>

    <!-- 第二步：手机号登录 -->
    <div v-if="currentStep === 2" class="step-container fade-in">
      <div class="back-header">
        <span class="btn-back" @click="goBack">← 返回</span>
        <span class="current-role">{{ roleNameMap[selectedRole] }}</span>
        <span class="placeholder-right"></span>
      </div>

      <div class="input-group">
        <input
          type="tel"
          v-model="phone"
          placeholder="请输入手机号"
          maxlength="11"
          autofocus
        />
      </div>

      <button class="btn-main" :disabled="loading" @click="handleLogin">
        {{ loading ? '正在登录…' : '手机号快捷登录' }}
      </button>

      <button class="btn-wechat" @click="wechatLogin">微信一键登录</button>

      <p class="tips">未注册的手机号将自动创建账号</p>
      <p v-if="errorText" class="err">{{ errorText }}</p>
      <p v-if="needMerchant" class="link-line" @click="goMerchantVerify">前往完成商家认证 ›</p>
    </div>

    <div class="bottom-roles" v-if="showAdminEntries">
      <span @click="goToAdmin('agent')">经纪人</span> |
      <span @click="goToAdmin('ops')">运营方</span> |
      <span @click="goToAdmin('gov')">监管方</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
import { useUserStore } from '../store/user'

const userStore = useUserStore()
const route = useRoute()

// 回跳地址（游客触发动作后被引导登录）
const redirectPath = typeof route.query.redirect === 'string' ? route.query.redirect : ''

// 意图角色：由触发动作的入口决定；没有就是空（走正常选角色流程）
const intentRole = computed(() => {
  const r = String(route.query.role || '').toLowerCase()
  return ['worker', 'merchant', 'provider'].includes(r) ? r : ''
})

const roleNameMap = { worker: '求职者登录', merchant: '招聘方登录', provider: '服务商登录' }

// 带意图 → 直接第二步；否则停留在选角色
const currentStep = ref(intentRole.value ? 2 : 1)
const selectedRole = ref(intentRole.value || '')

const phone = ref('')
const loading = ref(false)
const errorText = ref('')
const needMerchant = ref(false)

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
  errorText.value = ''
  needMerchant.value = false
  currentStep.value = 2
}

const goBack = () => {
  currentStep.value = 1
  selectedRole.value = ''
  errorText.value = ''
  needMerchant.value = false
}

function afterLogin() {
  if (redirectPath) {
    window.location.hash = '#' + (redirectPath.startsWith('/') ? redirectPath : '/' + redirectPath)
    return
  }
  if (selectedRole.value === 'provider') {
    window.location.hash = '#/provider/hall'
    return
  }
  if (selectedRole.value === 'merchant') {
    window.location.hash = '#/merchant/dash'
    return
  }
  window.location.hash = '#/worker/home'
}

const handleLogin = async () => {
  errorText.value = ''
  needMerchant.value = false
  if (!phone.value || phone.value.length < 11) return window.$toast('请输入正确的 11 位手机号')

  loading.value = true
  try {
    const res = await api.post('/auth/login', {
      phone: phone.value,
      target_role: selectedRole.value
    })
    userStore.setLogin(res.data, selectedRole.value)
    window.$toast('登录成功')
    setTimeout(afterLogin, 400)
  } catch (err) {
    const detail = err.response?.data?.detail || '登录失败，请检查网络'
    errorText.value = detail
    // 🚨 意图登录的安全兜底：账号没有该身份时，绝不把人放进错误的工作台
    if (selectedRole.value === 'merchant' && String(detail).includes('商家')) {
      needMerchant.value = true
    }
  } finally {
    loading.value = false
  }
}

function wechatLogin() {
  window.$toast('微信一键登录待接入，请先用手机号登录')
}

function goMerchantVerify() {
  window.location.hash = '#/merchant/verify'
}

// 管理端入口（真实登录）
const ADMIN_ROLE_MAP = { ops: 'hq_ops', gov: 'city_gov', agent: 'city_ops' }
const ADMIN_LABEL = { ops: '运营方', gov: '监管方', agent: '经纪人' }

const goToAdmin = async (role) => {
  const adminPhone = window.prompt(`请输入「${ADMIN_LABEL[role]}」管理员手机号`)
  if (!adminPhone) return
  if (adminPhone.length < 11) return window.$toast('请输入正确的 11 位手机号')

  try {
    const res = await api.post('/auth/login', {
      phone: adminPhone,
      target_role: ADMIN_ROLE_MAP[role]
    })
    userStore.setLogin(res.data, role)
  } catch (err) {
    return window.$toast(err.response?.data?.detail || '该手机号未开通管理端权限')
  }

  if (role === 'ops' || role === 'gov') {
    window.$toast('正在进入管理后台...')
    setTimeout(() => { window.location.hash = '#/admin/dash' }, 600)
  } else {
    window.$toast('正在跳转至资质审核...')
    setTimeout(() => { window.location.hash = '#/admin/audit' }, 600)
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  padding: 72px 30px 30px;
  background: #fff;
  display: flex;
  flex-direction: column;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
.logo-area { text-align: center; margin-bottom: 40px; cursor: pointer; user-select: none; }
.logo-area h1 { font-size: 30px; color: #ff6b00; font-weight: 800; margin-bottom: 10px; }
.logo-area p { color: #6b7280; font-size: 14px; }

.step-container { display: flex; flex-direction: column; flex: 1; }
.fade-in { animation: fadeIn 0.3s ease-in-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

.step-hint { text-align: center; font-size: 20px; font-weight: 800; color: #111; margin-bottom: 24px; }

.main-btns { display: flex; flex-direction: column; gap: 14px; }
.btn-main {
  padding: 17px;
  background: #ff6b00;
  color: #fff;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 800;
  border: none;
}
.btn-main:disabled { opacity: 0.65; }
.btn-sub {
  padding: 16px;
  background: #fff7f0;
  color: #ff6b00;
  border: 1px solid #ffd3b0;
  border-radius: 12px;
  font-size: 17px;
  font-weight: 700;
}

.btn-wechat {
  margin-top: 12px;
  padding: 15px;
  background: #f2fbf5;
  color: #0f9d58;
  border: 1px solid #b7e3c8;
  border-radius: 12px;
  font-size: 17px;
  font-weight: 700;
}

.back-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 26px;
  font-size: 18px;
  font-weight: 800;
  color: #111;
}
.btn-back { color: #8b95a5; font-size: 14px; font-weight: 400; }
.placeholder-right { width: 40px; }

.input-group { margin-bottom: 22px; }
.input-group input {
  width: 100%;
  padding: 16px;
  font-size: 18px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #f6f8fb;
  outline: none;
  text-align: center;
  letter-spacing: 2px;
  font-weight: 700;
  color: #333;
}
.input-group input:focus { border-color: #ff6b00; background: #fff; }

.tips { text-align: center; font-size: 12px; color: #9ca3af; margin-top: 16px; line-height: 1.6; }
.err { margin-top: 14px; text-align: center; font-size: 14px; color: #e5484d; line-height: 1.5; }
.link-line { margin-top: 10px; text-align: center; font-size: 15px; color: #ff6b00; font-weight: 700; }

.bottom-roles { margin-top: auto; text-align: center; padding-bottom: 16px; color: #6b7280; font-size: 14px; }
.bottom-roles span { cursor: pointer; margin: 0 8px; }
</style>
