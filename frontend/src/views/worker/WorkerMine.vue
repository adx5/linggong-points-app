<!-- frontend/src/views/worker/WorkerMine.vue —— 大字版「我的」
     游客态：只展示登录引导；登录后展示积分/投递/功能入口
     配色跟随主题（未登录蓝 / 登录橙）
-->
<template>
  <div class="mine-page">
    <!-- 顶部用户卡 -->
    <section class="mine-head">
      <div class="mine-user">
        <div class="mine-avatar">{{ avatarChar }}</div>
        <div class="mine-user-body">
          <h2 class="mine-name">{{ displayName }}</h2>
          <p class="mine-sub">
            <span v-if="!loggedIn">登录后可查看投递与积分</span>
            <span v-else-if="isVerified" class="mine-badge">已实名认证</span>
            <span v-else class="mine-warn" @click="goVerify">未实名，去认证 ›</span>
          </p>
        </div>
        <button v-if="!loggedIn" class="mine-login" @click="goLogin">登录 / 注册</button>
      </div>

      <div v-if="loggedIn" class="mine-stats">
        <div class="mine-stat" @click="go('/worker/points')">
          <b>{{ points }}</b><span>可用积分</span>
        </div>
        <div class="mine-stat" @click="go('/worker/my-applies')">
          <b>{{ applyCount }}</b><span>我的投递</span>
        </div>
        <div class="mine-stat" @click="go('/worker/service')">
          <b>去逛逛</b><span>同城服务</span>
        </div>
      </div>
    </section>

    <!-- 功能入口 -->
    <section class="mine-group">
      <h3 class="mine-group-title">我的求职</h3>
      <button v-for="item in jobMenus" :key="item.label" class="mine-row" @click="handle(item)">
        <span class="mine-ico">{{ item.icon }}</span>
        <span class="mine-label">{{ item.label }}</span>
        <span v-if="item.tip" class="mine-tip">{{ item.tip }}</span>
        <span class="mine-arrow">›</span>
      </button>
    </section>

    <section class="mine-group">
      <h3 class="mine-group-title">更多</h3>
      <button v-for="item in moreMenus" :key="item.label" class="mine-row" @click="handle(item)">
        <span class="mine-ico">{{ item.icon }}</span>
        <span class="mine-label">{{ item.label }}</span>
        <span class="mine-arrow">›</span>
      </button>
    </section>

    <div class="mine-actions">
      <button v-if="loggedIn" class="mine-btn ghost" @click="logout">退出登录 / 切换身份</button>
      <button v-else class="mine-btn primary" @click="goLogin">立即登录</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()

const loggedIn = ref(!!localStorage.getItem('token'))
const points = ref(0)
const applyCount = ref(0)
const realName = ref('')
const gender = ref('')
const isVerified = ref(false)

const avatarChar = computed(() => {
  if (isVerified.value && realName.value) return realName.value.charAt(0)
  return loggedIn.value ? '打' : '游'
})

const displayName = computed(() => {
  if (!loggedIn.value) return '未登录'
  if (isVerified.value && realName.value) {
    return `${realName.value}${gender.value === '女' ? '女士' : '先生'}`
  }
  return '超级打工人'
})

const jobMenus = [
  { icon: '📋', label: '我的投递', path: '/worker/my-applies', auth: true },
  { icon: '⭐', label: '我的收藏', path: '/worker/favorites', auth: false },
  { icon: '📝', label: '我的简历', path: '/worker/resume', auth: true },
  { icon: '🛡️', label: '实名认证', path: '/worker/verify', auth: true, tipKey: 'verify' },
  { icon: '💰', label: '积分明细', path: '/worker/points', auth: true }
]

const moreMenus = [
  { icon: '🎯', label: '每日任务', path: '/worker/task', auth: true },
  { icon: '🎁', label: '积分兑换', path: '/worker/exchange', auth: true },
  { icon: '🛠️', label: '同城服务', path: '/worker/service', auth: false },
  { icon: '🎧', label: '联系客服', action: 'service', auth: false }
]

function go(path) {
  router.push(path)
}

function goLogin() {
  router.push({ path: '/login', query: { role: 'worker', redirect: '/worker/mine' } })
}

function goVerify() {
  router.push('/worker/verify')
}

function handle(item) {
  if (item.auth && !loggedIn.value) {
    window.$toast && window.$toast('登录后即可使用')
    return goLogin()
  }
  if (item.action === 'service') {
    return window.$toast && window.$toast('客服电话：400-000-0000（示例）')
  }
  router.push(item.path)
}

async function load() {
  if (!loggedIn.value) return
  try {
    const res = await api.get('/user/points')
    points.value = res.data?.points || 0
  } catch (err) {}

  try {
    const res = await api.get('/jobs/my-applications')
    applyCount.value = Array.isArray(res.data) ? res.data.length : 0
  } catch (err) {}

  try {
    const res = await api.get('/user/profile')
    if (res.data?.verify_status === 'verified') {
      isVerified.value = true
      realName.value = res.data.real_name || ''
      gender.value = res.data.gender || ''
    }
  } catch (err) {}
}

function logout() {
  localStorage.clear()
  window.location.hash = '#/login'
  window.location.reload()
}

onMounted(load)
</script>

<style scoped>
.mine-page {
  min-height: 100vh;
  background: var(--bg, #eef1f5);
  padding: 14px 20px 90px;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* 顶部 */
.mine-head {
  background: #fff;
  border-radius: 18px;
  padding: 20px;
  box-shadow: var(--shadow-card, 0 4px 16px rgba(31, 79, 143, 0.08));
  margin-bottom: 14px;
}
.mine-user { display: flex; align-items: center; gap: 14px; }
.mine-avatar {
  width: 60px; height: 60px; border-radius: 50%;
  background: var(--brand, #1677ff); color: #fff;
  font-size: 24px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.mine-user-body { flex: 1; min-width: 0; }
.mine-name { font-size: 21px; font-weight: 800; color: var(--text, #1d2531); }
.mine-sub { font-size: 13px; color: var(--text-sub, #7b8797); margin-top: 5px; }
.mine-badge {
  display: inline-block;
  background: var(--brand-soft, #eaf2ff);
  color: var(--brand, #1677ff);
  font-weight: 700;
  padding: 2px 9px;
  border-radius: 6px;
}
.mine-warn { color: var(--price, #ff7a1a); font-weight: 700; }
.mine-login {
  border: none;
  background: var(--brand, #1677ff);
  color: #fff;
  height: 40px;
  padding: 0 18px;
  border-radius: 999px;
  font-size: 15px;
  font-weight: 800;
  flex-shrink: 0;
}

.mine-stats {
  display: flex;
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid #f2f4f7;
}
.mine-stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.mine-stat b { font-size: 20px; font-weight: 800; color: var(--brand, #1677ff); }
.mine-stat span { font-size: 12px; color: var(--text-sub, #7b8797); }

/* 分组 */
.mine-group {
  background: #fff;
  border-radius: 18px;
  padding: 6px 20px;
  margin-bottom: 14px;
  box-shadow: var(--shadow-card, 0 4px 16px rgba(31, 79, 143, 0.08));
}
.mine-group-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-sub, #7b8797);
  padding: 14px 0 6px;
}
.mine-row {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  border: none;
  background: none;
  padding: 15px 0;
  border-top: 1px solid #f7f9fb;
  text-align: left;
}
.mine-row:first-of-type { border-top: none; }
.mine-ico { font-size: 20px; width: 26px; text-align: center; }
.mine-label { flex: 1; font-size: 16px; font-weight: 600; color: var(--text, #1d2531); }
.mine-tip { font-size: 12px; color: var(--price, #ff7a1a); font-weight: 700; }
.mine-arrow { color: #c4ccd6; font-size: 18px; }

.mine-actions { padding: 6px 0 20px; }
.mine-btn {
  width: 100%;
  height: 50px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 800;
  border: none;
}
.mine-btn.ghost { background: #fff; color: #e5484d; border: 1px solid #f0f2f5; }
.mine-btn.primary { background: var(--brand, #1677ff); color: #fff; }
</style>
