<!-- frontend/src/layout/WorkerLayout.vue (C端骨架：大字版底部导航) -->
<template>
  <div class="layout-container">
    <router-view />
    <div class="bottom-nav">
      <div
        v-for="tab in tabs"
        :key="tab.path"
        class="tab"
        :class="{ active: isActive(tab) }"
        @click="$router.push(tab.path)"
      >
        <span class="icon">{{ tab.icon }}</span>
        <span>{{ tab.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

const tabs = [
  { path: '/worker/home', icon: '🏠', label: '首页', match: ['/worker/home'] },
  { path: '/worker/find', icon: '🔍', label: '找活', match: ['/worker/find', '/worker/long-term', '/worker/short-term', '/worker/job-detail'] },
  { path: '/worker/service', icon: '🛠️', label: '同城', match: ['/worker/service'] },
  { path: '/worker/mine', icon: '👤', label: '我的', match: ['/worker/mine'] }
]

function isActive(tab) {
  return tab.match.some((p) => route.path.startsWith(p))
}
</script>

<style scoped>
.layout-container { min-height: 100vh; padding-bottom: 65px; background: var(--bg, #eef1f5); }
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: #fff;
  display: flex;
  border-top: 1px solid #eef0f3;
  z-index: 999;
  padding-bottom: env(safe-area-inset-bottom);
}
.tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9aa6b5;
  font-size: 11px;
  cursor: pointer;
}
.tab.active { color: var(--brand, #1677ff); font-weight: 800; }
.icon { font-size: 20px; margin-bottom: 2px; }
</style>
