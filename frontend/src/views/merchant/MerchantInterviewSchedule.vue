<!-- (B端面试管理：当前面试 流转 + 面试记录 台账) -->
<template>
  <div class="interview-page">
    <div class="sticky-header">
      <h2>面试管理</h2>
    </div>

    <!-- 顶部一级 Tab -->
    <div class="main-tabs">
      <div class="m-tab" :class="{ active: mainTab === 'current' }" @click="mainTab = 'current'">
        当前面试 <span class="badge" v-if="currentList.length > 0">{{ currentList.length }}</span>
      </div>
      <div class="m-tab" :class="{ active: mainTab === 'history' }" @click="mainTab = 'history'">面试记录</div>
    </div>

    <div class="list-content">
      <div class="card" v-for="item in displayList" :key="item.id">
        <div class="row">
          <div class="user">
            <h3>{{ item.worker_name }}</h3>
            <p class="job-title">投递: {{ item.job_title }}</p>
          </div>
        </div>

        <!-- 当前面试区，处理动作 -->
        <template v-if="mainTab === 'current'">
          <div class="status-warn" v-if="item.status === 2">邀请已发出，等待求职者确认...</div>
          <div class="actions" v-else-if="item.status === 3">
            <button class="btn-reject" @click.stop="handle(item.id, 6)">不合适</button>
            <button class="btn-pass" @click.stop="handle(item.id, 5)">确认录用</button>
          </div>
        </template>

        <!-- 历史记录区，只看不操作 -->
        <div v-else class="status-done">
          {{ getStatusText(item.status) }}
        </div>
      </div>

      <div v-if="displayList.length === 0" class="empty">
        <p v-if="mainTab === 'current'">当前没有需要处理的面试排期</p>
        <p v-else>暂无面试历史记录</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api'

const mainTab = ref('current')
const allData = ref([])

const loadData = async () => {
  const res = await api.get('/jobs/received')
  // 只取面试相关的状态：2待面试，3已同意，4面试拒绝，5录用，6不合适
  allData.value = res.data.filter(item => [2, 3, 4, 5, 6].includes(item.status))
}

// 当前面试：待确认(2) + 已同意待处理(3)
const currentList = computed(() => {
  return allData.value.filter(item => [2, 3].includes(item.status))
})

// 面试记录：历史结果(4, 5, 6)
const historyList = computed(() => {
  return allData.value.filter(item => [4, 5, 6].includes(item.status))
})

const displayList = computed(() => {
  return mainTab.value === 'current' ? currentList.value : historyList.value
})

const getStatusText = (status) => {
  const map = { 2: '等待求职者确认', 3: '已同意，待录用', 4: '求职者已拒绝', 5: '已录用', 6: '不合适' }
  return map[status] || '未知'
}

const handle = async (id, status) => {
  await api.put(`/jobs/application/${id}?status=${status}`)
  window.$toast('操作成功')
  loadData()
}

onMounted(() => { loadData() })
</script>

<style scoped>
.interview-page { min-height: 100vh; background: #f0f2f5; }
.sticky-header { position: sticky; top: 0; z-index: 99; background: #fff; padding: 16px; border-bottom: 1px solid #eee; }
.sticky-header h2 { font-size: 18px; color: #1f2937; }

.main-tabs { display: flex; background: #fff; border-bottom: 1px solid #eee; }
.m-tab { flex: 1; text-align: center; padding: 14px 0; font-size: 15px; color: #666; cursor: pointer; font-weight: bold; position: relative; }
.m-tab.active { color: #2563eb; border-bottom: 2px solid #2563eb; }
.m-tab .badge { background: #ef4444; color: #fff; font-size: 11px; padding: 2px 6px; border-radius: 10px; margin-left: 4px; }

.list-content { padding: 16px; }
.card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
.row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.user h3 { font-size: 16px; color: #1f2937; margin-bottom: 6px; }
.job-title { font-size: 13px; color: #9ca3af; }

.status-warn { color: #f59e0b; font-weight: bold; text-align: center; padding: 10px; background: #fffbeb; border-radius: 6px; font-size: 14px; }
.status-done { color: #10b981; font-weight: bold; text-align: center; padding: 10px; background: #ecfdf5; border-radius: 6px; font-size: 14px; }

.actions { display: flex; gap: 12px; }
.actions button { flex: 1; padding: 10px; border-radius: 6px; font-weight: bold; border: none; font-size: 14px; cursor: pointer; }
.btn-reject { background: #fef2f2; color: #ef4444; border: 1px solid #fecaca !important; }
.btn-pass { background: #2563eb; color: #fff; }
.empty { text-align: center; padding: 60px 0; color: #9ca3af; font-size: 14px; }
</style>