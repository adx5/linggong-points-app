<!-- (B端骨架：黑底白字底部导航) -->
<template>
  <div class="layout-container">
    <router-view />

    <div class="bottom-nav">
      <div class="tab" :class="{ active: $route.path.includes('/merchant/dash') }" @click="$router.push('/merchant/dash')">
        <span>主页</span>
      </div>
      <div class="tab" :class="{ active: $route.path.includes('/merchant/job-list') || $route.path.includes('/merchant/job-create') }" @click="$router.push('/merchant/job-list')">
        <span>岗位管理</span>
      </div>
      <!-- 🚨 改名为：人才库 -->
      <div class="tab" :class="{ active: $route.path.includes('/merchant/talent-pool') }" @click="$router.push('/merchant/talent-pool')">
        <span>人才库</span>
      </div>
      <div class="tab" :class="{ active: $route.path.includes('/merchant/mine') || $route.path.includes('/merchant/received-resumes') }" @click="$router.push('/merchant/mine')">
        <span>我的企业</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.layout-container { min-height: 100vh; padding-bottom: 65px; background: #f0f2f5; }
.bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; height: 60px; background: #1f2937; display: flex; z-index: 999; padding-bottom: env(safe-area-inset-bottom); }
.tab { flex: 1; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size: 14px; }
.tab.active { color: #fff; font-weight: bold; background: rgba(255,255,255,0.1); }
</style>