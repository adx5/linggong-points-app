<!-- frontend/src/views/worker/WorkerPoints.vue (C端积分明细) -->
<template>
  <div class="points-page">
    <div class="sticky-header">
      <div class="header-left">
        <div class="btn-back" @click="$router.back()">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#1f2937" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
        </div>
        <h2>积分明细</h2>
      </div>
    </div>

    <div class="points-card">
      <div class="label">当前可用积分</div>
      <div class="val">{{ totalPoints }}</div>
    </div>

    <div class="list">
      <div v-if="history.length === 0" class="empty">暂无积分记录</div>
      <div class="history-item" v-for="item in history" :key="item.id">
        <div class="item-left">
          <h4>{{ item.remark }}</h4>
          <p>{{ item.created_at }}</p>
        </div>
        <div class="item-right">
          <span :class="['amount', item.amount > 0 ? 'plus' : 'minus']">
            {{ item.amount > 0 ? '+' : '' }}{{ item.amount }}
          </span>
          <p class="balance">余额 {{ item.balance_after }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const totalPoints = ref(0)
const history = ref([])

onMounted(async () => {
  try {
    const resPts = await api.get('/user/points')
    totalPoints.value = resPts.data.points
  } catch (err) {}

  try {
    const resHistory = await api.get('/user/points/history')
    history.value = resHistory.data || []
  } catch (err) {}
})
</script>

<style scoped>
.points-page { min-height: 100vh; background: #f5f6f8; padding-bottom: 20px; }
.sticky-header { position: sticky; top: 0; z-index: 99; background: #fff; padding: 16px; border-bottom: 1px solid #eee; }
.header-left { display: flex; align-items: center; gap: 8px; }
.btn-back { cursor: pointer; display: flex; align-items: center; margin-left: -8px; }
.sticky-header h2 { font-size: 18px; color: #1f2937; font-weight: bold; }

.points-card { background: linear-gradient(135deg, #3b82f6, #2dd4bf); margin: 16px; padding: 24px; border-radius: 12px; color: #fff; text-align: center; }
.points-card .label { font-size: 14px; opacity: 0.9; margin-bottom: 8px; }
.points-card .val { font-size: 36px; font-weight: bold; }

.list { padding: 0 16px; }
.history-item { display: flex; justify-content: space-between; align-items: center; background: #fff; padding: 16px; border-radius: 8px; margin-bottom: 12px; }
.item-left h4 { font-size: 15px; color: #1f2937; margin-bottom: 6px; }
.item-left p { font-size: 12px; color: #9ca3af; }
.item-right { text-align: right; }
.amount { font-size: 18px; font-weight: bold; }
.amount.plus { color: #10b981; }
.amount.minus { color: #ef4444; }
.balance { font-size: 12px; color: #9ca3af; margin-top: 4px; }
.empty { text-align: center; color: #9ca3af; padding: 40px 0; }
</style>