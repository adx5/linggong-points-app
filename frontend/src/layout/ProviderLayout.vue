<!-- frontend/src/layout/ProviderLayout.vue (服务商端骨架：绿色主题) -->
<template>
  <div class="provider-layout" :class="{ 'no-nav': !showNav }">
    <router-view />
    <div v-if="showNav" class="pn-bottom">
      <div
        v-for="tab in tabs"
        :key="tab.path"
        class="pn-tab"
        :class="{ active: isActive(tab) }"
        @click="$router.push(tab.path)"
      >
        <span class="pn-icon">{{ tab.icon }}</span>
        <span>{{ tab.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const tabs = [
  { path: '/provider/hall', icon: '💬', label: '招聘大厅', match: ['/provider/hall'] },
  { path: '/provider/services', icon: '📋', label: '服务管理', match: ['/provider/services', '/provider/publish'] },
  { path: '/provider/mine', icon: '👤', label: '我的', match: ['/provider/mine', '/provider/verify', '/provider/homepage', '/provider/settings'] }
]

// 一键直发是沉浸式向导：原型里没有底部导航，靠自己的操作栏推进
const showNav = computed(() => route.path !== '/provider/publish')

function isActive(tab) {
  return tab.match.some((p) => route.path.startsWith(p))
}
</script>

<style scoped>
/* 服务商端设计令牌（绿色系，原型 #00C853） */
.provider-layout {
  --g: #00c853;
  --g-soft: #e8f5e9;
  --g-text: #009a44;
  --warn: #fa8c16;
  --warn-soft: #fffbe6;
  --danger: #f53f3f;
  --bg: #f5f7fa;
  --text: #111;
  --line: #e5e6eb;
  min-height: 100vh;
  padding-bottom: 62px;
  background: var(--bg);
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.provider-layout.no-nav { padding-bottom: 0; }

.pn-bottom {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  height: 60px;
  background: #fff;
  display: flex;
  border-top: 1px solid #eef0f3;
  z-index: 999;
  padding-bottom: env(safe-area-inset-bottom);
}
.pn-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  color: #9aa6b5;
  font-size: 11px;
  cursor: pointer;
}
.pn-tab.active { color: var(--g); font-weight: 800; }
.pn-icon { font-size: 20px; }
</style>
