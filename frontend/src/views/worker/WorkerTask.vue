<!-- frontend/src/views/worker/WorkerTask.vue (任务中心：透传后端报错) -->
<template>
  <div class="task-page">
    <div class="header">
      <h2>任务中心</h2>
    </div>

    <div class="points-card">
      <div class="label">当前可用积分</div>
      <div class="val">{{ points }}</div>
    </div>

    <div class="task-list">
      <div class="task-item">
        <div class="info">
          <h4>看视频赚积分</h4>
          <p>每次观看完整视频可得 5 积分</p>
        </div>
        <button @click="watchAd" class="btn-ad" :disabled="isWatching">
          {{ isWatching ? '加载中...' : '去观看' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const points = ref(0)
const isWatching = ref(false)

const getPoints = async () => {
  try {
    const res = await api.get('/user/points')
    points.value = res.data.points
  } catch (err) { console.error(err) }
}

const watchAd = async () => {
  isWatching.value = true
  try {
    const tokenRes = await api.post('/ads/get-token', {}, {
      headers: { 'X-Client-Type': 'app' }
    })
    const adToken = tokenRes.data.ad_token

    const res = await api.post('/ads/watch-ad', { ad_token: adToken })

    window.$toast(res.message)
    getPoints()
  } catch (err) {
    const errorMsg = err.response?.data?.detail || '网络异常，请稍后重试'
    window.$toast(errorMsg)
  } finally {
    isWatching.value = false
  }
}

onMounted(() => { getPoints() })
</script>

<style scoped>
.task-page { min-height: 100vh; background: #f5f6f8; }
.header { background: #fff; padding: 16px; border-bottom: 1px solid #eee; }
.header h2 { font-size: 18px; }
.points-card { background: linear-gradient(135deg, #3b82f6, #2dd4bf); margin: 16px; padding: 24px; border-radius: 12px; color: #fff; text-align: center; }
.points-card .label { font-size: 14px; opacity: 0.9; margin-bottom: 8px; }
.points-card .val { font-size: 36px; font-weight: bold; }
.task-list { padding: 0 16px; }
.task-item { background: #fff; border-radius: 12px; padding: 16px; display: flex; justify-content: space-between; align-items: center; }
.info h4 { font-size: 15px; margin-bottom: 4px; }
.info p { font-size: 12px; color: #999; }
.btn-ad { background: #10b981; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; }
.btn-ad:disabled { background: #a7f3d0; }
</style>