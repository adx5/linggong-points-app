<!-- frontend/src/views/provider/ProviderMine.vue —— 服务商端「我的」 -->
<template>
  <div class="pm-page">
    <section class="pm-head">
      <div class="pm-avatar">{{ avatarChar }}</div>
      <div class="pm-body">
        <h2 class="pm-name">{{ displayName }}</h2>
        <p class="pm-sub">{{ roleText }}</p>
      </div>
      <span class="pm-verify">{{ verified ? '已认证' : '待认证' }}</span>
    </section>

    <section class="pm-stats">
      <div class="pm-stat"><b>{{ serviceCount }}</b><span>在架服务</span></div>
      <div class="pm-stat"><b>{{ orderCount }}</b><span>进行中订单</span></div>
      <div class="pm-stat"><b>{{ rating }}</b><span>综合评分</span></div>
    </section>

    <section class="pm-group">
      <button v-for="m in menus" :key="m.label" class="pm-row" @click="handle(m)">
        <span class="pm-ico">{{ m.icon }}</span>
        <span class="pm-label">{{ m.label }}</span>
        <span class="pm-arrow">›</span>
      </button>
    </section>

    <div class="pm-actions">
      <button class="pm-btn danger" @click="logout">退出登录</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()

const displayName = ref('服务商')
const avatarChar = ref('服')
const roleText = ref('本地生活服务商')
const verified = ref(false)
const rating = ref('—')
const serviceCount = ref(0)
const orderCount = ref(0)

const menus = [
  { icon: '🛡️', label: '资质与实名认证', path: '/provider/verify' },
  { icon: '🏪', label: '我的主页展示', path: '/provider/homepage' },
  { icon: '📄', label: '服务管理', path: '/provider/services' },
  { icon: '⚙️', label: '设置', path: '/provider/settings' },
  { icon: '🎧', label: '联系客服', action: 'service' }
]

async function load() {
  try {
    const me = await api.get('/user/profile')
    if (me.data?.real_name) {
      displayName.value = me.data.real_name
      avatarChar.value = me.data.real_name.charAt(0)
    }
    verified.value = me.data?.verify_status === 'verified'
  } catch (err) {}

  try {
    const s = await api.get('/services/my-services')
    serviceCount.value = (s.data || []).filter((x) => x.status === 'active').length
  } catch (err) {}

  try {
    const o = await api.get('/services/orders/provider', { params: { status: 'accepted' } })
    orderCount.value = (o.data || []).length
  } catch (err) {}

  try {
    const list = await api.get('/services/providers')
    const uid = Number(localStorage.getItem('userId') || 0)
    const mine = (list.data || []).find((p) => p.display_name === displayName.value)
    if (mine) rating.value = mine.rating
  } catch (err) {}
}

function handle(m) {
  if (m.path) return router.push(m.path)
  if (m.action === 'service') {
    window.location.href = 'tel:4000000000'
  }
}

function logout() {
  localStorage.clear()
  window.location.hash = '#/login'
  window.location.reload()
}

onMounted(load)
</script>

<style scoped>
.pm-page { min-height: 100vh; background: var(--bg); padding: 14px 20px 90px; }

.pm-head {
  display: flex;
  align-items: center;
  gap: 14px;
  background: linear-gradient(135deg, #00c853, #00a844);
  border-radius: 18px;
  padding: 20px;
  color: #fff;
}
.pm-avatar {
  width: 58px;
  height: 58px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 800;
  flex-shrink: 0;
}
.pm-body { flex: 1; min-width: 0; }
.pm-name { font-size: 21px; font-weight: 800; }
.pm-sub { font-size: 13px; opacity: 0.9; margin-top: 4px; }
.pm-verify {
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.22);
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
}

.pm-stats {
  display: flex;
  background: #fff;
  border-radius: 16px;
  padding: 16px 0;
  margin-top: 14px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}
.pm-stat { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.pm-stat b { font-size: 20px; font-weight: 800; color: var(--g-text); }
.pm-stat span { font-size: 12px; color: #7b8797; }

.pm-group {
  background: #fff;
  border-radius: 16px;
  padding: 4px 20px;
  margin-top: 14px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}
.pm-row {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
  border: none;
  border-top: 1px solid #f7f9fb;
  background: none;
  text-align: left;
}
.pm-row:first-child { border-top: none; }
.pm-ico { font-size: 20px; width: 26px; text-align: center; }
.pm-label { flex: 1; font-size: 16px; font-weight: 600; color: var(--text); }
.pm-arrow { color: #c4ccd6; font-size: 18px; }

.pm-actions { margin-top: 20px; display: flex; flex-direction: column; gap: 12px; }
.pm-btn { width: 100%; height: 50px; border-radius: 12px; font-size: 16px; font-weight: 800; border: none; }
.pm-btn.ghost { background: #fff; color: var(--g-text); border: 1px solid #d9f2e3; }
.pm-btn.danger { background: #fff; color: var(--danger); border: 1px solid #f0f2f5; }
</style>
