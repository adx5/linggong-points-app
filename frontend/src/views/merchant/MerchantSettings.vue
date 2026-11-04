<!-- frontend/src/views/merchant/MerchantSettings.vue (B端设置中心：修复退出登录) -->
<template>
  <div class="settings-page">
    <div class="sticky-header">
      <h2>设置中心</h2>
    </div>

    <div class="menu-list">
      <div class="menu-item" @click="handleClick('账号安全')">
        <span>账号安全</span>
        <span class="arrow">></span>
      </div>
      <div class="menu-item" @click="handleClick('发票管理')">
        <span>发票管理</span>
        <span class="arrow">></span>
      </div>
      <div class="menu-item" @click="handleClick('联系平台客服')">
        <span>联系平台客服</span>
        <span class="arrow">></span>
      </div>
      <div class="menu-item" @click="handleClick('关于平台')">
        <span>关于平台</span>
        <span class="version">v1.0.0</span>
      </div>
    </div>

    <div class="action-area">
      <span class="btn-logout-text" @click="logout">退出登录 / 切换身份</span>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()

const handleClick = (title) => {
  window.$toast(`【${title}】功能即将开放，敬请期待`)
}

const logout = () => {
  localStorage.clear()
  // 🚨 修复：使用 Hash 模式跳转
  window.location.hash = '#/login'
  window.location.reload()
}
</script>

<style scoped>
.settings-page { min-height: 100vh; background: #f0f2f5; display: flex; flex-direction: column; }
.sticky-header { position: sticky; top: 0; z-index: 99; background: #fff; padding: 16px; border-bottom: 1px solid #eee; }
.sticky-header h2 { font-size: 18px; color: #1f2937; }
.menu-list { background: #fff; margin: 16px; border-radius: 12px; padding: 0 16px; }
.menu-item { display: flex; justify-content: space-between; padding: 18px 0; border-bottom: 1px solid #f3f4f6; font-size: 15px; color: #333; cursor: pointer; }
.menu-item:last-child { border-bottom: none; }
.menu-item:active { background: #f9fafb; }
.arrow { color: #ccc; }
.version { font-size: 14px; color: #9ca3af; }
.action-area { display: flex; justify-content: center; margin-top: auto; padding: 20px 0; }
.btn-logout-text { font-size: 13px; color: #94a3b8; padding: 8px 20px; cursor: pointer; }
.btn-logout-text:active { color: #64748b; }
</style>