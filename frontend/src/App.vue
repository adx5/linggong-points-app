<!-- (根组件：包含全局Toast、路由出口) -->
<template>
  <router-view />
  <!-- 直接使用全局响应式状态控制 Toast -->
  <Toast v-if="toastVisible" :msg="toastMessage" />
</template>

<script setup>
import Toast from './components/Toast.vue'
import { toastVisible, toastMessage, showToast } from './utils/toast'

// 兼容你现有页面里写的一堆 window.$toast
window.$toast = showToast
</script>