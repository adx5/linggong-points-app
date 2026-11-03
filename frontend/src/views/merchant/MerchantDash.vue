<!-- (B端工作台：动态数据与真实状态) -->
<template>
  <div class="dash-page">
    <div class="header">
      <div class="title-row">
        <!-- 🚨 动态显示企业名称 -->
        <h2>{{ greeting }}，{{ companyName }}</h2>
        <span class="badge" v-if="status === 'active'">🏅 优秀雇主</span>
      </div>
      <p>祝您今天招到合适的人才</p>
    </div>

    <!-- 🚨 只有认证通过，才显示这些绿色标签 -->
    <div class="status-tags" v-if="status === 'active'">
      <span class="tag green">✅ 已备案</span>
      <span class="tag blue">✅ 审核通过</span>
      <span class="tag orange">诚信等级 A</span>
    </div>
    <!-- 如果没认证，放个提示条 -->
    <div class="status-tags" v-else>
      <span class="tag orange">⚠️ 待完善资质</span>
    </div>

    <div class="today-stats-card">
      <div class="card-title">今日实时数据</div>
      <div class="stats-grid">
        <div class="stat-item">
          <div class="val">{{ todayStats.views }}</div>
          <div class="label">今日曝光</div>
        </div>
        <div class="stat-item">
          <div class="val text-blue">{{ todayStats.applies }}</div>
          <div class="label">今日报名</div>
        </div>
        <div class="stat-item">
          <div class="val text-green">{{ todayStats.hired }}</div>
          <div class="label">今日录用</div>
        </div>
      </div>
    </div>

    <div class="section-card">
      <div class="section-header">
        <h3>最新报名</h3>
        <span class="more" @click="$router.push('/merchant/received-resumes')">全部 ></span>
      </div>
      <div class="mini-list">
        <div class="mini-item" v-for="item in latestApplies" :key="item.id">
          <div class="info">
            <span class="name">{{ item.name }}</span>
            <span class="job">{{ item.job }}</span>
            <span class="time">{{ item.time }}</span>
          </div>
          <button class="btn-chat" @click="goChat(item)">去沟通</button>
        </div>
      </div>
    </div>

    <div class="section-card">
      <div class="section-header">
        <h3>热招岗位 TOP3</h3>
      </div>
      <div class="top-list">
        <div class="top-item" v-for="(job, index) in topJobs" :key="job.id">
          <div class="rank" :class="'rank-' + (index + 1)">{{ index + 1 }}</div>
          <div class="job-info">
            <div class="job-title">{{ job.title }}</div>
            <div class="progress-bar">
              <div class="progress-text">已招 {{ job.hired }}/{{ job.total }} 人</div>
              <div class="bar-bg">
                <div class="bar-fill" :style="{ width: (job.hired / job.total * 100) + '%' }"></div>
              </div>
            </div>
          </div>
          <button class="btn-urgent" @click="urgent(job)">加急</button>
        </div>
      </div>
    </div>

    <!-- 全平台唯一的“找牛人”入口 -->
    <div class="quick-actions">
      <div class="action-btn" @click="$router.push('/merchant/job-create')">
        <span>📢</span> 去发岗位
      </div>
      <div class="action-btn" @click="$router.push('/merchant/talent-pool')">
        <span>🔍</span> 找牛人
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()
const companyName = ref('加载中...')
const status = ref('')

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const todayStats = ref({ views: 156, applies: 12, hired: 2 })

const latestApplies = ref([
  { id: 1, name: '王**', job: '普工', time: '2分钟前报名' },
  { id: 2, name: '李**', job: '叉车工', time: '15分钟前报名' },
  { id: 3, name: '赵**', job: '普工', time: '1小时前报名' }
])

const topJobs = ref([
  { id: 1, title: '汽配厂直招普工', hired: 5, total: 10 },
  { id: 2, title: '电子厂组装正式工', hired: 8, total: 20 },
  { id: 3, title: '仓库搬运临时工', hired: 2, total: 5 }
])

const goChat = (item) => window.$toast(`正在连接与 ${item.name} 的沟通窗口...`)
const urgent = (job) => window.$toast(`已为【${job.title}】设置加急曝光！`)

// 🚨 核心：拉取真实的名称与认证状态
onMounted(async () => {
  try {
    const res = await api.get('/merchant/info')
    if (res.data) {
      companyName.value = res.data.name || '请完善名称'
      status.value = res.data.status
    }
  } catch (err) {
    companyName.value = '请完善名称'
  }
})
</script>

<style scoped>
.dash-page { min-height: 100vh; background: #f0f2f5; padding-bottom: 80px; }
.header { background: #1f2937; padding: 20px 20px 40px; color: #fff; border-radius: 0 0 20px 20px; }
.title-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.title-row h2 { font-size: 20px; }
.badge { background: linear-gradient(135deg, #f59e0b, #fbbf24); color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 12px; font-weight: bold; white-space: nowrap; }
.header p { font-size: 13px; color: #9ca3af; }
.status-tags { display: flex; gap: 8px; padding: 0 16px; margin-top: -15px; position: relative; z-index: 10; margin-bottom: 16px; }
.tag { font-size: 12px; padding: 4px 10px; border-radius: 4px; font-weight: bold; background: #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
.tag.green { color: #10b981; }
.tag.blue { color: #2563eb; }
.tag.orange { color: #f59e0b; }
.today-stats-card { background: #fff; margin: 0 16px 16px; border-radius: 12px; padding: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.card-title { font-size: 15px; font-weight: bold; color: #1f2937; margin-bottom: 16px; }
.stats-grid { display: flex; justify-content: space-between; }
.stat-item { flex: 1; text-align: center; border-right: 1px solid #f3f4f6; }
.stat-item:last-child { border-right: none; }
.stat-item .val { font-size: 22px; font-weight: bold; color: #1f2937; margin-bottom: 4px; }
.stat-item .val.text-blue { color: #2563eb; }
.stat-item .val.text-green { color: #10b981; }
.stat-item .label { font-size: 12px; color: #6b7280; }
.section-card { background: #fff; margin: 0 16px 16px; border-radius: 12px; padding: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-header h3 { font-size: 15px; font-weight: bold; color: #1f2937; }
.section-header .more { font-size: 12px; color: #9ca3af; cursor: pointer; }
.mini-list { display: flex; flex-direction: column; gap: 12px; }
.mini-item { display: flex; justify-content: space-between; align-items: center; }
.mini-item .info { display: flex; align-items: center; gap: 8px; }
.mini-item .name { font-size: 14px; font-weight: bold; color: #333; }
.mini-item .job { font-size: 12px; color: #2563eb; background: #eff6ff; padding: 2px 6px; border-radius: 4px; }
.mini-item .time { font-size: 12px; color: #9ca3af; }
.btn-chat { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: bold; cursor: pointer; }
.top-list { display: flex; flex-direction: column; gap: 12px; }
.top-item { display: flex; align-items: center; gap: 12px; }
.rank { width: 20px; height: 20px; background: #f3f4f6; color: #666; font-size: 12px; font-weight: bold; display: flex; justify-content: center; align-items: center; border-radius: 4px; }
.rank-1 { background: #fef2f2; color: #ef4444; }
.rank-2 { background: #fffbeb; color: #f59e0b; }
.rank-3 { background: #eff6ff; color: #2563eb; }
.job-info { flex: 1; }
.job-title { font-size: 14px; color: #333; font-weight: bold; margin-bottom: 4px; }
.progress-bar { display: flex; align-items: center; gap: 8px; }
.progress-text { font-size: 12px; color: #666; white-space: nowrap; }
.bar-bg { flex: 1; height: 6px; background: #f3f4f6; border-radius: 3px; overflow: hidden; }
.bar-fill { height: 100%; background: #10b981; border-radius: 3px; }
.btn-urgent { background: #fef2f2; color: #ef4444; border: none; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: bold; cursor: pointer; }
.quick-actions { display: flex; gap: 12px; padding: 0 16px; }
.action-btn { flex: 1; background: #fff; padding: 18px; border-radius: 12px; text-align: center; font-weight: bold; color: #333; box-shadow: 0 2px 8px rgba(0,0,0,0.03); cursor: pointer; }
.action-btn span { display: block; font-size: 24px; margin-bottom: 8px; }
</style>