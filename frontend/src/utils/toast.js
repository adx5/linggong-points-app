// (跨端 Toast 状态管理，彻底替代 window.$toast)
import { ref } from 'vue'

// 全局共享的响应式状态
export const toastVisible = ref(false)
export const toastMessage = ref('')

let timer = null

export const showToast = (msg, duration = 2000) => {
  toastMessage.value = msg
  toastVisible.value = true

  if (timer) clearTimeout(timer)

  timer = setTimeout(() => {
    toastVisible.value = false
  }, duration)
}