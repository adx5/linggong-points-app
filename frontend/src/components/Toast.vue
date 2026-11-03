<!-- (全局轻提示组件：优雅的黑色小药丸弹窗) -->
<template>
  <div v-if="visible" class="toast-box">
    {{ msg }}
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { toastVisible, toastMessage } from '../utils/toast'

const visible = computed(() => toastVisible.value)
const msg = computed(() => toastMessage.value)
</script>

<style scoped>
.toast-box {
  position: fixed;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.75);
  color: #fff;
  padding: 12px 24px;
  border-radius: 24px;
  font-size: 14px;
  z-index: 99999;
  text-align: center;
  max-width: 80%;
  word-break: break-all;
  /* 增加一点淡入淡出动画 */
  animation: fadeIn 0.2s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>