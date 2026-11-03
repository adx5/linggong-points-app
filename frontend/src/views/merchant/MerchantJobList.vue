<!-- (B端岗位管理列表：严格依靠认证状态分配Tab，含手动上架) -->
<template>
  <div class="job-list-page">
    <div class="sticky-header">
      <h2>岗位管理</h2>
      <button class="btn-create" @click="$router.push('/merchant/job-create')">+ 发岗位</button>
    </div>

    <!-- Tabs: 草稿箱 -> 在招 -> 停招 -->
    <div class="tabs">
      <div class="tab" :class="{ active: currentTab === 'draft' }" @click="currentTab = 'draft'">草稿箱</div>
      <div class="tab" :class="{ active: currentTab === 'active' }" @click="currentTab = 'active'">在招岗位</div>
      <div class="tab" :class="{ active: currentTab === 'stopped' }" @click="currentTab = 'stopped'">已停招</div>
    </div>

    <div class="list-content">
      <!-- 🚨 草稿箱顶部提示（只有未认证时显示） -->
      <div v-if="currentTab === 'draft' && !isVerified" class="pending-tip">
        完成企业备案后，草稿箱中的岗位将自动解锁。
        <span @click="$router.push('/merchant/verify')" style="color:#2563eb; font-weight:bold; cursor:pointer;">去备案 ></span>
      </div>
      <!-- 🚨 草稿箱顶部提示（已认证但未上架时显示） -->
      <div v-if="currentTab === 'draft' && isVerified" class="success-tip">
        ✅ 您的企业已认证通过，可点击下方【立即上架】按钮将岗位展示给求职者。
      </div>

      <!-- 岗位卡片列表 -->
      <div class="job-card" v-for="item in filteredJobs" :key="item.id">
        <div class="card-header">
          <h3>
            {{ item.title }}
            <span v-if="currentTab === 'draft'" class="status-tag-pending">草稿</span>
          </h3>
          <span class="salary">{{ item.salary }}</span>
        </div>

        <div class="meta-info">
          <div class="tags">
            <span v-for="tag in (item.tags || '').split(',').filter(t=>t)" :key="tag">{{ tag }}</span>
          </div>
          <div class="time-refresh-row">
            <span class="update-time">{{ currentTab === 'draft' ? '刚刚编辑' : '刚刚更新' }}</span>
            <span v-if="currentTab === 'active'" class="btn-refresh-text" @click="refreshJob(item)">刷新</span>
          </div>
        </div>

        <!-- 数据漏斗 (只有在招才看数据) -->
        <div class="data-funnel" v-if="currentTab === 'active'">
          <div class="data-item"><span class="val">0</span><span class="label">曝光</span></div>
          <div class="data-item"><span class="val">0</span><span class="label">报名</span></div>
          <div class="data-item"><span class="val">0</span><span class="label">面试</span></div>
          <div class="data-item"><span class="val text-green">0</span><span class="label">录用</span></div>
        </div>

        <!-- 统一风格的底部操作区 -->
        <div class="card-actions">
          <button class="btn-share" v-if="currentTab === 'active'" @click="shareJob(item)">📤 生成海报</button>

          <div class="right-actions">
            <!-- 🚨 如果是草稿，且企业已经认证了，出现发布按钮 -->
            <button class="btn-gray text-green" v-if="currentTab === 'draft' && isVerified" @click.stop="publishJob(item)">立即上架</button>

            <button class="btn-gray" v-if="currentTab === 'draft'">编辑</button>
            <button class="btn-gray" v-else-if="currentTab === 'active'">编辑</button>

            <!-- 草稿箱里是删除，在招里是停招 -->
            <button class="btn-gray text-red" v-if="currentTab === 'draft'" @click.stop="confirmDelete(item)">删除</button>
            <button class="btn-gray text-blue" v-else-if="currentTab === 'active'">下架停招</button>
            <button class="btn-gray text-blue" v-else-if="currentTab === 'stopped'">重新上架</button>
          </div>
        </div>
      </div>

      <!-- 空状态处理 -->
      <div v-if="filteredJobs.length === 0" class="empty-state">
        <div class="empty-icon">📭</div>
        <p v-if="currentTab === 'active'">暂无在招岗位，快去发布吧~</p>
        <p v-else-if="currentTab === 'draft'">草稿箱空空如也，暂无未完成的岗位</p>
        <p v-else>暂无已停招的历史岗位</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api'

const currentTab = ref('active')
const rawJobs = ref([])
const isVerified = ref(false)

const loadJobs = async () => {
  try {
    const res = await api.get('/jobs/my-list')
    rawJobs.value = res.data || []
    isVerified.value = res.is_verified

    // 🚨 如果未认证，且当前停留在在招岗位，强制切回草稿箱
    if (!isVerified.value && currentTab.value === 'active') {
      currentTab.value = 'draft'
    }
  } catch (err) {
    window.$toast('获取岗位失败')
  }
}

// 🚨 核心分配逻辑
const filteredJobs = computed(() => {
  return rawJobs.value.filter(job => {
    if (currentTab.value === 'active') return isVerified.value
    if (currentTab.value === 'draft') return !isVerified.value
    if (currentTab.value === 'stopped') return false
    return false
  })
})

// 🚨 手动上架功能
const publishJob = async (item) => {
  try {
    const res = await api.put(`/jobs/${item.id}/publish`)
    window.$toast(res.message || '岗位已成功上架')
    // 刷新列表，草稿会自动飞去“在招岗位”
    loadJobs()
  } catch (err) {
    window.$toast('上架失败，请确认企业是否已通过审核')
  }
}

const refreshJob = (item) => window.$toast('刷新成功，排序已提升')
const shareJob = (item) => window.$toast('正在生成招聘海报...')
const confirmDelete = (item) => {
  if (window.confirm(`确认删除草稿【${item.title}】吗？`)) {
    window.$toast('Demo阶段暂未开放真实删除接口')
  }
}

onMounted(() => { loadJobs() })
</script>

<style scoped>
.job-list-page { min-height: 100vh; background: #f0f2f5; }
.sticky-header { position: sticky; top: 0; z-index: 99; background: #fff; padding: 16px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }
.sticky-header h2 { font-size: 18px; color: #1f2937; }
.btn-create { background: #2563eb; color: #fff; padding: 8px 16px; border-radius: 6px; font-weight: bold; border: none; cursor: pointer; }

.tabs { display: flex; background: #fff; border-bottom: 1px solid #eee; }
.tab { flex: 1; text-align: center; padding: 12px 0; font-size: 14px; color: #666; cursor: pointer; transition: all 0.2s; }
.tab.active { color: #2563eb; font-weight: bold; border-bottom: 2px solid #2563eb; }

.list-content { padding: 16px; }

/* 提示条 */
.pending-tip { background: #fffbeb; color: #b45309; font-size: 13px; padding: 10px; border-radius: 6px; margin-bottom: 12px; border: 1px solid #fde68a; }
.success-tip { background: #ecfdf5; color: #10b981; font-size: 13px; padding: 10px; border-radius: 6px; margin-bottom: 12px; border: 1px solid #a7f3d0; }

.job-card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
.card-header { display: flex; justify-content: space-between; margin-bottom: 8px; align-items: flex-start; }
.card-header h3 { font-size: 16px; color: #1f2937; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.salary { color: #ef4444; font-weight: bold; font-size: 15px; white-space: nowrap; }

.status-tag-pending { font-size: 12px; background: #e5e7eb; color: #4b5563; padding: 2px 6px; border-radius: 4px; font-weight: normal; }

.meta-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tags span { font-size: 11px; background: #eff6ff; color: #2563eb; padding: 2px 6px; border-radius: 4px; }
.time-refresh-row { display: flex; align-items: center; gap: 8px; }
.update-time { font-size: 12px; color: #9ca3af; }
.btn-refresh-text { font-size: 12px; color: #2563eb; cursor: pointer; }

.data-funnel { display: flex; background: #f9fafb; border-radius: 8px; padding: 12px 0; margin-bottom: 12px; }
.data-item { flex: 1; text-align: center; display: flex; flex-direction: column; gap: 4px; border-right: 1px solid #e5e7eb; }
.data-item:last-child { border-right: none; }
.data-item .val { font-size: 16px; font-weight: bold; color: #333; }
.data-item .val.text-green { color: #10b981; }
.data-item .label { font-size: 12px; color: #999; }

.card-actions { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-top: 4px; }
.btn-share { flex: 1; background: #10b981; color: #fff; padding: 8px 0; border-radius: 6px; font-size: 13px; font-weight: bold; border: none; cursor: pointer; display: flex; justify-content: center; align-items: center; gap: 4px; }
.right-actions { display: flex; gap: 8px; }
.btn-gray { background: #fff; color: #374151; border: 1px solid #d1d5db; padding: 8px 14px; border-radius: 6px; font-size: 13px; font-weight: bold; cursor: pointer; }
.btn-gray.text-red { color: #ef4444; border-color: #fca5a5; }
.btn-gray.text-blue { color: #2563eb; border-color: #bfdbfe; }
/* 🚨 新增绿色上架按钮样式 */
.btn-gray.text-green { color: #10b981; border-color: #a7f3d0; }
.btn-gray.text-green:active { background: #ecfdf5; }

.empty-state { text-align: center; padding: 60px 0; color: #9ca3af; }
.empty-icon { font-size: 40px; margin-bottom: 12px; opacity: 0.5; }
.empty-state p { font-size: 14px; }
</style>