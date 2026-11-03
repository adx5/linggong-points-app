<!-- (Admin骨架：政务风底部导航) -->
<template>
  <div class="layout-container">
    <router-view />
    <div class="bottom-nav">
      <div class="tab" :class="{ active: $route.path.includes('/admin/dash') }" @click="$router.push('/admin/dash')">
        <span>工作台</span>
      </div>
      <div class="tab" :class="{ active: $route.path.includes('/admin/audit') }" @click="$router.push('/admin/audit')">
        <span>审核中心</span>
      </div>
      <!-- 🚨 新增：岗位风控专页 -->
      <div class="tab" :class="{ active: $route.path.includes('/admin/risk') }" @click="$router.push('/admin/risk')">
        <span>岗位风控</span>
      </div>
      <div class="tab" :class="{ active: $route.path.includes('/admin/gov') }" @click="$router.push('/admin/gov')">
        <span>监管大屏</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.layout-container { min-height: 100vh; padding-bottom: 65px; background: #f0f4f8; }
.bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; height: 60px; background: #ffffff; border-top: 1px solid #e5e7eb; display: flex; z-index: 999; padding-bottom: env(safe-area-inset-bottom); }
.tab { flex: 1; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 14px; cursor: pointer; }
.tab.active { color: #0052d9; font-weight: bold; }
</style>