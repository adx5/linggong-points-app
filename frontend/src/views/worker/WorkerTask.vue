<!-- frontend/src/views/worker/WorkerTask.vue —— 任务中心（推广赚积分 + 看视频赚积分） -->
<template>
  <div class="task-page">
    <header class="task-header">
      <h2>任务中心</h2>
      <p>做任务赚积分，积分可兑换或提现</p>
    </header>

    <section class="task-points">
      <div class="task-points-label">当前可用积分</div>
      <div class="task-points-val">{{ points }}</div>
    </section>

    <!-- 推广赚积分 -->
    <section class="task-card">
      <div class="task-card-head">
        <h3>推广岗位赚积分</h3>
        <span class="task-badge">每单 +{{ promo.reward_points }}</span>
      </div>
      <p class="task-desc">
        把岗位分享给工友，对方通过你的链接投递并**完成结单**后，积分自动到账。
      </p>

      <div class="task-stats">
        <div class="task-stat">
          <b>{{ promo.promoted }}</b><span>已推广</span>
        </div>
        <div class="task-stat">
          <b>{{ promo.settled }}</b><span>已结算</span>
        </div>
        <div class="task-stat">
          <b class="hl">+{{ promo.total_points }}</b><span>推广积分</span>
        </div>
      </div>

      <div v-if="promo.records && promo.records.length" class="task-records">
        <div v-for="r in promo.records" :key="r.application_id" class="task-record">
          <span class="task-record-title">{{ r.job_title }}</span>
          <span class="task-record-meta">{{ r.finished_at }} 已结单 +{{ promo.reward_points }}</span>
        </div>
      </div>

      <button class="task-btn" @click="goPromote">去推广岗位</button>
    </section>

    <!-- 看视频 -->
    <section class="task-card">
      <div class="task-card-head">
        <h3>看视频赚积分</h3>
        <span class="task-badge gray">每次 +5</span>
      </div>
      <p class="task-desc">完整观看一次视频，可得 5 积分（每日上限 20 次）。</p>
      <button class="task-btn ghost" :disabled="isWatching" @click="watchAd">
        {{ isWatching ? '加载中…' : '去观看' }}
      </button>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()

const points = ref(0)
const isWatching = ref(false)
const promo = ref({ reward_points: 20, promoted: 0, settled: 0, total_points: 0, records: [] })

async function loadPoints() {
  try {
    const res = await api.get('/user/points')
    points.value = res.data?.points || 0
  } catch (err) {}
}

async function loadPromotion() {
  try {
    const res = await api.get('/tasks/promotion')
    promo.value = res.data || promo.value
  } catch (err) {}
}

function goPromote() {
  router.push('/worker/find')
}

async function watchAd() {
  isWatching.value = true
  try {
    const tokenRes = await api.post('/ads/get-token', {}, { headers: { 'X-Client-Type': 'app' } })
    const adToken = tokenRes.data.ad_token

    const res = await api.post('/ads/watch-ad', { ad_token: adToken })
    window.$toast && window.$toast(res.message)
    await loadPoints()
  } catch (err) {
    window.$toast && window.$toast(err.response?.data?.detail || '网络异常，请稍后重试')
  } finally {
    isWatching.value = false
  }
}

onMounted(() => {
  loadPoints()
  loadPromotion()
})
</script>

<style scoped>
.task-page {
  min-height: 100vh;
  background: var(--bg, #eef1f5);
  padding: 16px 20px 30px;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.task-header h2 { font-size: 22px; font-weight: 800; color: var(--text, #1d2531); }
.task-header p { font-size: 13px; color: var(--text-sub, #7b8797); margin-top: 6px; }

.task-points {
  margin-top: 16px;
  background: linear-gradient(135deg, var(--brand, #1677ff), color-mix(in srgb, var(--brand, #1677ff) 70%, #fff));
  border-radius: 18px;
  padding: 20px;
  color: #fff;
}
.task-points-label { font-size: 13px; opacity: 0.9; }
.task-points-val { font-size: 34px; font-weight: 800; margin-top: 6px; }

.task-card {
  margin-top: 14px;
  background: #fff;
  border-radius: 18px;
  padding: 18px 20px;
  box-shadow: var(--shadow-card, 0 4px 16px rgba(31, 79, 143, 0.08));
}
.task-card-head { display: flex; align-items: center; justify-content: space-between; }
.task-card-head h3 { font-size: 18px; font-weight: 800; color: var(--text, #1d2531); }
.task-badge {
  background: var(--price-soft, #fff1e6);
  color: var(--price, #ff7a1a);
  font-size: 13px;
  font-weight: 800;
  padding: 4px 10px;
  border-radius: 6px;
}
.task-badge.gray { background: var(--bg, #eef1f5); color: #555; }

.task-desc { font-size: 13px; color: #7b8797; line-height: 1.7; margin: 10px 0 14px; }

.task-stats { display: flex; background: #f9fafc; border-radius: 14px; padding: 14px 0; }
.task-stat { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.task-stat b { font-size: 20px; font-weight: 800; color: var(--brand, #1677ff); }
.task-stat b.hl { color: var(--price, #ff7a1a); }
.task-stat span { font-size: 12px; color: #7b8797; }

.task-records { margin-top: 14px; }
.task-record {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 0;
  border-top: 1px solid #f2f4f7;
  font-size: 13px;
}
.task-record-title { color: var(--text, #1d2531); font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.task-record-meta { color: var(--price, #ff7a1a); flex-shrink: 0; }

.task-btn {
  margin-top: 16px;
  width: 100%;
  height: 50px;
  border: none;
  border-radius: 12px;
  background: var(--brand, #1677ff);
  color: #fff;
  font-size: 16px;
  font-weight: 800;
}
.task-btn.ghost { background: var(--bg, #eef1f5); color: #555; }
.task-btn:disabled { opacity: 0.6; }
</style>
