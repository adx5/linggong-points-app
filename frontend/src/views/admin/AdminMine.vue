<!-- frontend/src/views/admin/AdminMine.vue (Admin个人中心：修复退出登录) -->
<template>
  <div class="admin-mine">
    <div class="header">
      <div class="avatar">{{ isGov ? '监' : '运' }}</div>
      <div class="info">
        <h3>{{ currentRole.title }}</h3>
        <p>{{ currentRole.sub }}</p>
      </div>
    </div>

    <div class="menu-list">
      <div class="menu-item"><span>平台规则配置</span><span class="arrow">></span></div>
      <div class="menu-item"><span>操作日志审计</span><span class="arrow">></span></div>
      <div class="menu-item"><span>系统设置</span><span class="arrow">></span></div>
    </div>

    <div class="action-area">
      <span class="btn-logout-text" @click="logout">退出登录 / 切换身份</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const role = ref(localStorage.getItem('activeRole') || 'ops')
const isGov = computed(() => role.value === 'gov')

const currentRole = computed(() => {
  if (isGov.value) {
    return { title: '合规审核专员', sub: '政务穿透与资质审核' }
  }
  return { title: '平台运营专员', sub: '平台业务与日常管理' }
})

const logout = () => {
  localStorage.clear();
  // 🚨 修复：使用 Hash 模式跳转
  window.location.hash = '#/login';
  window.location.reload();
}
</script>

<style scoped>
.admin-mine { min-height: 100vh; background: #f0f4f8; display: flex; flex-direction: column; }
.header { background: #0052d9; padding: 40px 20px 30px; display: flex; align-items: center; gap: 15px; color: #ffffff; }
.avatar { width: 60px; height: 60px; background: #ffffff; color: #0052d9; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 24px; font-weight: bold; }
.info h3 { font-size: 20px; margin-bottom: 4px; }
.info p { font-size: 12px; opacity: 0.8; }
.menu-list { background: #ffffff; margin: 16px; border-radius: 12px; padding: 0 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
.menu-item { display: flex; justify-content: space-between; padding: 18px 0; border-bottom: 1px solid #f3f4f6; font-size: 15px; color: #333333; cursor: pointer; }
.menu-item:last-child { border-bottom: none; }
.arrow { color: #9ca3af; }
.action-area { display: flex; justify-content: center; margin-top: auto; padding: 20px 0; }
.btn-logout-text { font-size: 13px; color: #9ca3af; padding: 8px 20px; cursor: pointer; }
.btn-logout-text:active { color: #6b7280; }
</style>