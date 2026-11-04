<!-- frontend/src/views/merchant/MerchantMine.vue (B端我的企业：修复退出登录) -->
<template>
  <div class="mine-page">
    <div class="header">
      <div class="avatar">企</div>
      <div class="info">
        <h3>{{ companyName }}</h3>
        <p v-if="status === 'active'" class="status-verified">✅ 已认证企业</p>
        <p v-else-if="status === 'pending'" class="status-unverified" style="color:#f59e0b;">⏳ 审核中</p>
        <p v-else-if="status === 'rejected'" class="status-unverified" style="color:#ef4444;">❌ 已驳回</p>
        <p v-else class="status-unverified">⚠️ 未认证</p>
      </div>
    </div>

    <div v-if="status !== 'active'" class="alert-banner" @click="$router.push('/merchant/verify')">
      <template v-if="status === 'rejected'">
        您的备案被驳回：<span style="color:red">{{ rejectReason }}</span>。点击立即修改 >
      </template>
      <template v-else>
        当前企业未认证/待审核，岗位存入草稿箱。点击去备案 >
      </template>
    </div>

    <div class="stats-bar">
      <div class="stat-item"><span class="val">2</span><span class="label">在招岗位</span></div>
      <div class="stat-item"><span class="val">{{ resumeCount }}</span><span class="label">收到简历</span></div>
    </div>

    <div class="grid-menu">
      <div class="grid-item" @click="$router.push('/merchant/job-create')">
        <div class="icon-wrap" style="background:#f3e8ff; color:#8b5cf6;">📢</div><span>发布岗位</span>
      </div>
      <div class="grid-item" @click="$router.push('/merchant/job-list')">
        <div class="icon-wrap" style="background:#ecfdf5; color:#10b981;">💼</div><span>在招岗位</span>
      </div>

      <div class="grid-item" @click="$router.push('/merchant/received-resumes')">
        <div class="icon-wrap" style="background:#eff6ff; color:#2563eb;">📄</div>
        <span>收到简历</span>
        <span class="badge" v-if="resumeCount > 0">{{ resumeCount }}</span>
      </div>

      <div class="grid-item" @click="$router.push('/merchant/messages')">
        <div class="icon-wrap" style="background:#fef3c7; color:#f59e0b;">🔔</div>
        <span>消息通知</span>
        <span class="badge" v-if="unreadCount > 0">{{ unreadCount }}</span>
      </div>

      <div class="grid-item" @click="$router.push('/merchant/interviews')">
        <div class="icon-wrap" style="background:#e0f2fe; color:#0ea5e9;">📅</div>
        <span>面试管理</span>
        <span class="badge" v-if="interviewCount > 0">{{ interviewCount }}</span>
      </div>

      <div class="grid-item" @click="$router.push('/merchant/reviews')">
        <div class="icon-wrap" style="background:#f1f5f9; color:#64748b;">⭐</div><span>零工评价</span>
      </div>
      <div class="grid-item" @click="$router.push('/merchant/company')">
        <div class="icon-wrap" style="background:#fce7f3; color:#ec4899;">🏢</div><span>企业信息</span>
      </div>
      <div class="grid-item" @click="$router.push('/merchant/settings')">
        <div class="icon-wrap" style="background:#fee2e2; color:#ef4444;">⚙️</div><span>账号设置</span>
      </div>
    </div>

    <div class="action-area"><span class="btn-logout-text" @click="logout">退出登录 / 切换身份</span></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()
const status = ref('')
const companyName = ref('加载中...')
const rejectReason = ref('')
const unreadCount = ref(0)
const resumeCount = ref(0)
const interviewCount = ref(0)

onMounted(async () => {
  try {
    const res = await api.get('/merchant/info')
    if (res.data) {
      companyName.value = res.data.name || '请完善名称'
      status.value = res.data.status
      rejectReason.value = res.data.reject_reason
    }
  } catch (err) { companyName.value = '获取失败' }

  try {
    const notiRes = await api.get('/notifications/unread-count')
    unreadCount.value = notiRes.data.count
  } catch (err) {}

  try {
    const resumeRes = await api.get('/jobs/received-count')
    resumeCount.value = resumeRes.data.count
  } catch (err) {}

  try {
    const interviewRes = await api.get('/jobs/interview-count')
    interviewCount.value = interviewRes.data.count
  } catch (err) {}
})

const logout = () => {
  localStorage.clear()
  // 🚨 修复：使用 Hash 模式跳转
  window.location.hash = '#/login'
  window.location.reload()
}
</script>

<style scoped>
.mine-page { min-height: 100vh; background: #f0f2f5; display: flex; flex-direction: column; padding-bottom: 80px; }
.header { background: #1f2937; padding: 30px 20px 20px; color: #fff; display: flex; align-items: center; gap: 15px; }
.avatar { width: 60px; height: 60px; background: #fff; color: #1f2937; border-radius: 8px; display: flex; justify-content: center; align-items: center; font-size: 24px; font-weight: bold; }
.info h3 { font-size: 20px; margin-bottom: 4px; }
.status-verified { font-size: 12px; color: #10b981; }
.alert-banner { background: #fffbeb; color: #b45309; font-size: 13px; padding: 10px 16px; border-bottom: 1px solid #fde68a; cursor: pointer; display: flex; justify-content: space-between; }
.stats-bar { display: flex; background: #fff; margin: 12px 16px 16px; border-radius: 12px; padding: 15px; position: relative; z-index: 10; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.stat-item { flex: 1; text-align: center; display: flex; flex-direction: column; gap: 4px; }
.stat-item .val { font-size: 20px; font-weight: bold; color: #2563eb; }
.stat-item .label { font-size: 12px; color: #6b7280; }
.grid-menu { background: #fff; margin: 16px; border-radius: 12px; padding: 20px 10px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
.grid-item { position: relative; text-align: center; font-size: 13px; color: #333; display: flex; flex-direction: column; align-items: center; gap: 8px; cursor: pointer; }
.icon-wrap { width: 44px; height: 44px; border-radius: 12px; display: flex; justify-content: center; align-items: center; font-size: 20px; }
.badge { position: absolute; top: -2px; right: 10px; background: #ef4444; color: #fff; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px; border: 2px solid #fff; }
.action-area { display: flex; justify-content: center; margin-top: auto; padding: 20px 0 10px 0; }
.btn-logout-text { font-size: 13px; color: #94a3b8; padding: 8px 20px; cursor: pointer; }
</style>