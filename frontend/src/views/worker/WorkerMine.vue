<!-- (C端个人中心：包含完整工作台，无快捷切换身份入口) -->
<template>
  <div class="mine-page">
    <!-- 顶部用户信息 -->
    <div class="header">
      <div class="user-info">
        <div class="avatar">打</div>
        <div class="info">
          <h3>超级打工人</h3>
          <p>求职者身份</p>
        </div>
      </div>
      <div class="stats">
        <div class="stat-item">
          <span class="val">{{ points }}</span>
          <span class="label">可用积分</span>
        </div>
        <div class="stat-item">
          <span class="val">0</span>
          <span class="label">投递中</span>
        </div>
      </div>
    </div>

    <!-- 功能九宫格 -->
    <div class="grid-menu">
      <div class="grid-item" @click="$router.push('/worker/my-applies')">
        <div class="icon-wrap" style="background:#eff6ff; color:#2563eb;">📋</div>
        <span>我的投递</span>
      </div>
      <div class="grid-item" @click="$router.push('/worker/task')">
        <div class="icon-wrap" style="background:#fef3c7; color:#f59e0b;">🎯</div>
        <span>每日任务</span>
      </div>
      <div class="grid-item" @click="$router.push('/worker/exchange')">
        <div class="icon-wrap" style="background:#fce7f3; color:#ec4899;">🎁</div>
        <span>积分兑换</span>
      </div>
      <div class="grid-item">
        <div class="icon-wrap" style="background:#dcfce7; color:#10b981;">⏱️</div>
        <span>记工时</span>
      </div>
      <div class="grid-item">
        <div class="icon-wrap" style="background:#f3e8ff; color:#8b5cf6;">👥</div>
        <span>零工人脉</span>
      </div>
      <div class="grid-item">
        <div class="icon-wrap" style="background:#e0f2fe; color:#0ea5e9;">📝</div>
        <span>简历维护</span>
      </div>
      <div class="grid-item">
        <div class="icon-wrap" style="background:#fee2e2; color:#ef4444;">🔧</div>
        <span>我的工单</span>
      </div>
      <div class="grid-item">
        <div class="icon-wrap" style="background:#f1f5f9; color:#64748b;">🎧</div>
        <span>联系客服</span>
      </div>
    </div>

    <!-- 底部操作区：只保留退出登录 -->
    <div class="action-area">
      <button class="btn-logout" @click="logout">退出登录 / 切换身份</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()
const points = ref(0)

onMounted(async () => {
  try {
    const res = await api.get('/user/points')
    points.value = res.data.points
  } catch (err) {}
})

const logout = () => {
  localStorage.clear()
  router.replace('/login')
}
</script>

<style scoped>
.mine-page { min-height: 100vh; background: #f5f6f8; padding-bottom: 80px; }
.header { background: linear-gradient(135deg, #3b82f6, #2dd4bf); padding: 30px 20px; color: #fff; border-radius: 0 0 20px 20px; }
.user-info { display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }
.avatar { width: 60px; height: 60px; background: #fff; color: #2563eb; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 24px; font-weight: bold; }
.info h3 { font-size: 20px; margin-bottom: 4px; }
.info p { font-size: 13px; opacity: 0.9; }
.stats { display: flex; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 15px; }
.stat-item { flex: 1; text-align: center; display: flex; flex-direction: column; gap: 4px; }
.stat-item .val { font-size: 20px; font-weight: bold; }
.stat-item .label { font-size: 12px; opacity: 0.8; }

.grid-menu { background: #fff; margin: 16px; border-radius: 12px; padding: 20px 10px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
.grid-item { text-align: center; font-size: 13px; color: #333; display: flex; flex-direction: column; align-items: center; gap: 8px; cursor: pointer; }
.grid-item:active { opacity: 0.7; }
.icon-wrap { width: 44px; height: 44px; border-radius: 12px; display: flex; justify-content: center; align-items: center; font-size: 20px; }

.action-area { padding: 0 16px; margin-top: 30px; }
.btn-logout { width: 100%; background: #fff; color: #ef4444; padding: 15px; border-radius: 8px; font-weight: bold; font-size: 15px; border: 1px solid #eee; }
</style>