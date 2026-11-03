<!-- (C端骨架：白底蓝字底部导航) -->
<template>
  <div class="layout-container">
    <router-view />
    <div class="bottom-nav">
      <div class="tab" :class="{ active: $route.path.includes('/worker/home') }" @click="$router.push('/worker/home')">
        <span class="icon">🏠</span><span>首页</span>
      </div>
      <div class="tab" :class="{ active: $route.path.includes('/worker/long-term') }" @click="$router.push('/worker/long-term')">
        <span class="icon">💼</span><span>长期稳定</span>
      </div>
      <div class="tab" :class="{ active: $route.path.includes('/worker/short-term') }" @click="$router.push('/worker/short-term')">
        <span class="icon">⚡</span><span>短期灵活</span>
      </div>
      <div class="tab" :class="{ active: $route.path.includes('/worker/mine') }" @click="$router.push('/worker/mine')">
        <span class="icon">👤</span><span>我的</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.layout-container { min-height: 100vh; padding-bottom: 65px; background: #f5f6f8; }
.bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; height: 60px; background: #fff; display: flex; border-top: 1px solid #eee; z-index: 999; padding-bottom: env(safe-area-inset-bottom); }
.tab { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #999; font-size: 11px; }
.tab.active { color: #2563eb; font-weight: bold; }
.icon { font-size: 20px; margin-bottom: 2px; }
</style>