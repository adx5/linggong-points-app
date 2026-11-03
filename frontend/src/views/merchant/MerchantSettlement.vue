<!-- (B端用工结算：履约中 + 待评价/已完成) -->
<template>
  <div class="settlement-page">
    <div class="sticky-header">
      <h2>用工结算与评价</h2>
    </div>

    <div class="main-tabs">
      <div class="m-tab" :class="{ active: mainTab === 'working' }" @click="mainTab = 'working'">履约中</div>
      <div class="m-tab" :class="{ active: mainTab === 'review' }" @click="mainTab = 'review'">待评价/已完成</div>
    </div>

    <div class="list-content">
      <div class="card" v-for="item in displayList" :key="item.id">
        <div class="info">
          <h3>{{ item.worker_name }}</h3>
          <p>{{ item.job_title }} | 完工时间: {{ item.finish_time || '进行中' }}</p>
        </div>

        <div class="action">
          <!-- 履约中 -->
          <div v-if="item.status === 5" class="status-working">履约中，等待工人完工申请...</div>

          <!-- 待评价 (C端申请完结单 或 已完工但没打分) -->
          <div v-if="item.status === 7 || (item.status === 8 && !item.star)" class="pending-box">
            <div class="stars">
              <span v-for="i in 5" :key="i" @click="setStar(item, i)" :class="{ active: i <= item.currentStar }">★</span>
            </div>
            <button class="btn-submit" @click="confirmAndReview(item)">
              {{ item.status === 7 ? '确认完工并评价' : '提交评价' }}
            </button>
          </div>

          <!-- 已完成 -->
          <div v-if="item.status === 8 && item.star" class="status-working">已完工，评分：{{ item.star }} 星</div>
        </div>
      </div>

      <div v-if="displayList.length === 0" class="empty">
        <p v-if="mainTab === 'working'">暂无履约中的工人</p>
        <p v-else>暂无待评价或已完成的记录</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api'

const mainTab = ref('working')
const list = ref([])

const loadData = async () => {
  const res = await api.get('/jobs/received')
  const raw = res.data.filter(item => [5, 7, 8].includes(item.status))

  const reviewRes = await api.get('/jobs/pending-reviews')
  list.value = raw.map(item => {
    const isRated = item.status === 8 && !reviewRes.data.some(r => r.application_id === item.id)
    return { ...item, currentStar: 5, star: isRated ? 5 : null }
  })
}

const displayList = computed(() => {
  if (mainTab.value === 'working') return list.value.filter(item => item.status === 5)
  return list.value.filter(item => [7, 8].includes(item.status))
})

const setStar = (item, star) => { item.currentStar = star }

const confirmAndReview = async (item) => {
  if (!item.currentStar) return window.$toast('请先打分')
  try {
    if (item.status === 7) {
      await api.put(`/jobs/application/${item.id}/confirm-finish`)
    }
    await api.post('/jobs/review', { application_id: item.id, rating: item.currentStar, comment: "" })
    window.$toast('已完工并评价成功')
    loadData()
  } catch (err) {
    window.$toast(err.response?.data?.detail || '操作失败')
  }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.settlement-page { min-height: 100vh; background: #f0f2f5; }
.sticky-header { position: sticky; top: 0; z-index: 99; background: #fff; padding: 16px; border-bottom: 1px solid #eee; }
.sticky-header h2 { font-size: 18px; color: #1f2937; }

.main-tabs { display: flex; background: #fff; border-bottom: 1px solid #eee; }
.m-tab { flex: 1; text-align: center; padding: 14px 0; font-size: 15px; color: #666; cursor: pointer; font-weight: bold; }
.m-tab.active { color: #2563eb; border-bottom: 2px solid #2563eb; }

.list-content { padding: 16px; }
.card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
.info { border-bottom: 1px solid #f3f4f6; padding-bottom: 12px; margin-bottom: 12px; }
.info h3 { font-size: 16px; color: #1f2937; margin-bottom: 4px; }
.info p { font-size: 13px; color: #666; }
.status-working { color: #3b82f6; font-weight: bold; text-align: center; padding: 10px; background: #eff6ff; border-radius: 6px; font-size: 14px; }
.pending-box { display: flex; justify-content: space-between; align-items: center; background: #fffbeb; padding: 10px; border-radius: 6px; }
.stars { font-size: 20px; color: #e5e7eb; cursor: pointer; }
.stars span.active { color: #f59e0b; }
.btn-submit { background: #2563eb; color: #fff; padding: 6px 16px; border-radius: 6px; font-size: 13px; font-weight: bold; border: none; cursor: pointer; }
.empty { text-align: center; padding: 60px 0; color: #9ca3af; font-size: 14px; }
</style>