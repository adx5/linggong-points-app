<!-- (全局图标组件：支持平滑切换 Emoji / 图片 / Iconfont) -->
<template>
  <span class="app-icon">{{ iconContent }}</span>
</template>

<script setup>
import { computed } from 'vue'
import { iconMap } from '../utils/iconMap'

const props = defineProps({
  name: { type: String, required: true }
})

// 目前返回 Emoji，后期如果是图片，可以改成返回 img 路径并在 template 渲染 <img>
const iconContent = computed(() => iconMap[props.name] || '')
</script>

<style scoped>
.app-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>