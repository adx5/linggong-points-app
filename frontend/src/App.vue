<!-- frontend/src/App.vue (根组件：启动闪屏 + 全局Toast + 路由出口) -->
<template>
  <router-view />

  <!-- P1 闪屏：每个会话首次进入展示一次，点击可跳过 -->
  <transition name="splash-fade">
    <div v-if="splashVisible" class="splash" @click="dismissSplash">
      <div class="splash-logo">零工<br />市场</div>
      <p class="splash-slogan">找活快，结钱准</p>
    </div>
  </transition>

  <!-- 直接使用全局响应式状态控制 Toast -->
  <Toast v-if="toastVisible" :msg="toastMessage" />
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import Toast from './components/Toast.vue'
import { toastVisible, toastMessage, showToast } from './utils/toast'

// 兼容你现有页面里写的一堆 window.$toast
window.$toast = showToast

// ---------- P1 闪屏 ----------
const SPLASH_KEY = 'splash_shown'
const DURATION = 1100

const splashVisible = ref(!sessionStorage.getItem(SPLASH_KEY))
let timer = null

function dismissSplash() {
  splashVisible.value = false
  sessionStorage.setItem(SPLASH_KEY, '1')
  if (timer) clearTimeout(timer)
}

onMounted(() => {
  if (!splashVisible.value) return
  timer = setTimeout(dismissSplash, DURATION)
})

onBeforeUnmount(() => {
  if (timer) clearTimeout(timer)
})
</script>

<style scoped>
.splash {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: var(--brand, #1677ff);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 22px;
}
.splash-logo {
  width: 120px;
  height: 120px;
  border-radius: 24px;
  background: #fff;
  color: var(--brand, #1677ff);
  font-size: 30px;
  font-weight: 800;
  line-height: 1.2;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
}
.splash-slogan {
  color: #fff;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 3px;
}

.splash-fade-leave-active { transition: opacity 0.35s ease; }
.splash-fade-leave-to { opacity: 0; }
</style>
