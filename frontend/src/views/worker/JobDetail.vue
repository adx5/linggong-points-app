<!-- (C端岗位详情页：四色状态矩阵时间轴，补齐完整日期) -->
<template>
  <div class="detail-page" v-if="job.id">
    <div class="nav-bar">
      <div class="btn-back" @click="$router.back()">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#1f2937" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
      </div>
      <span>岗位详情</span>
    </div>

    <div class="header-card">
      <div class="title-row">
        <h2>{{ job.title }}</h2>
        <span class="price">{{ job.salary }}</span>
      </div>
      <div class="tags">
        <span class="primary-tag">{{ job.filter_tag }}</span>
        <span v-for="tag in job.tags.split(',')" :key="tag">{{ tag }}</span>
      </div>
      <p class="loc">📍 {{ job.location }}</p>
    </div>

    <div class="section-card" v-if="myApp.id">
      <h3>我的应聘进度</h3>

      <div class="timeline">
        <!-- 节点 1 -->
        <div class="tl-node" :class="getNodeData(1).type">
          <div class="dot"></div>
          <div class="text">{{ getNodeData(1).title }}</div>
          <div class="status-text" v-if="getNodeData(1).status">{{ getNodeData(1).status }}</div>
          <div class="date" v-if="getNodeData(1).date">{{ getNodeData(1).date }}</div>
        </div>

        <div class="tl-line" :class="getLineData(1)"></div>

        <!-- 节点 2 -->
        <div class="tl-node" :class="getNodeData(2).type">
          <div class="dot"></div>
          <div class="text">{{ getNodeData(2).title }}</div>
          <div class="status-text" v-if="getNodeData(2).status">{{ getNodeData(2).status }}</div>
          <div class="date" v-if="getNodeData(2).date">{{ getNodeData(2).date }}</div>
        </div>

        <div class="tl-line" :class="getLineData(2)"></div>

        <!-- 节点 3 -->
        <div class="tl-node" :class="getNodeData(3).type">
          <div class="dot"></div>
          <div class="text">{{ getNodeData(3).title }}</div>
          <div class="status-text" v-if="getNodeData(3).status">{{ getNodeData(3).status }}</div>
          <div class="date" v-if="getNodeData(3).date">{{ getNodeData(3).date }}</div>
        </div>

        <div class="tl-line" :class="getLineData(3)"></div>

        <!-- 节点 4 -->
        <div class="tl-node" :class="getNodeData(4).type">
          <div class="dot"></div>
          <div class="text">{{ getNodeData(4).title }}</div>
          <div class="status-text" v-if="getNodeData(4).status">{{ getNodeData(4).status }}</div>
          <div class="date" v-if="getNodeData(4).date">{{ getNodeData(4).date }}</div>
        </div>

        <div class="tl-line" :class="getLineData(4)"></div>

        <!-- 节点 5 -->
        <div class="tl-node" :class="getNodeData(5).type">
          <div class="dot"></div>
          <div class="text">{{ getNodeData(5).title }}</div>
          <div class="status-text" v-if="getNodeData(5).status">{{ getNodeData(5).status }}</div>
          <div class="date" v-if="getNodeData(5).date">{{ getNodeData(5).date }}</div>
        </div>
      </div>
    </div>

    <div class="section-card">
      <h3>人员要求</h3>
      <p class="text-content">{{ job.requirement || '暂无特殊要求' }}</p>
      <h3 style="margin-top: 15px;">岗位介绍</h3>
      <p class="text-content">{{ job.description || '暂无介绍' }}</p>
    </div>

    <div class="bottom-bar">
      <button class="btn-call" @click="callPhone">电话咨询</button>
      <button class="btn-apply" disabled v-if="myApp.status === '不合适' || myApp.status === '面试已拒绝'" style="background: #9ca3af;">流程已结束</button>
      <button class="btn-apply" disabled v-else-if="myApp.id" style="background: #10b981; color: white;">已投递</button>
      <button class="btn-apply" @click="apply" v-else>立即投递</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../api'

const route = useRoute()
const job = ref({})
const company = ref({})
const phone = ref('13800000000')
const myApp = ref({})
const appStatus = ref(0)

const loadDetail = async () => {
  try {
    const res = await api.get(`/jobs/${route.params.id}`)
    job.value = res.data.job
    company.value = res.data.company

    const appRes = await api.get('/jobs/my-applications')
    const currentApp = appRes.data.find(a => a.job_id === job.value.id)

    if (currentApp) {
      myApp.value = currentApp
      const statusMap = { "待处理": 1, "不合适": 1, "待面试": 2, "面试已拒绝": 2, "面试已同意": 3, "已录用": 4, "申请结单中": 4, "结单争议": 4, "已完工": 5 };
      appStatus.value = statusMap[currentApp.status] || 1
    }
  } catch (err) { console.error(err) }
}

const formatDate = (dateTimeStr) => {
  if (!dateTimeStr) return ''
  return dateTimeStr.split(' ')[0]
}

// 🚨 核心逻辑：严格分离 标题、状态、日期
const getNodeData = (index) => {
  const s = myApp.value.status;
  // 默认结构
  let data = { title: '', status: '', date: '', type: 'wait' };
  const baseNames = ['投递', '初筛', '面试', '录用', '完工'];
  data.title = baseNames[index - 1];

  // 1. 待处理 (B端在看简历)
  if (s === '待处理') {
    if (index === 1) data = { title: '已投递', date: formatDate(myApp.value.created_at), type: 'success' };
    if (index === 2) data = { title: '初筛', status: '进行中', type: 'processing' };
  }
  // 2. 不合适 (B端初筛淘汰)
  else if (s === '不合适') {
    if (index === 1) data = { title: '已投递', date: formatDate(myApp.value.created_at), type: 'success' };
    // 如果后端没返回 invite_time，用 updated_at 兜底，证明被拒的时间
    if (index === 2) data = { title: '初筛', status: '未通过', date: formatDate(myApp.value.invite_time || myApp.value.updated_at), type: 'danger' };
  }
  // 3. 待面试 (B端通过初筛，等C端决策)
  else if (s === '待面试') {
    if (index === 1) data = { title: '已投递', date: formatDate(myApp.value.created_at), type: 'success' };
    if (index === 2) data = { title: '已初筛', date: formatDate(myApp.value.invite_time), type: 'success' };
    if (index === 3) data = { title: '面试', status: '进行中', type: 'processing' };
  }
  // 4. 面试已拒绝 (C端放弃了面试)
  else if (s === '面试已拒绝') {
    if (index === 1) data = { title: '已投递', date: formatDate(myApp.value.created_at), type: 'success' };
    if (index === 2) data = { title: '已初筛', date: formatDate(myApp.value.invite_time), type: 'success' };
    if (index === 3) data = { title: '面试', status: '已放弃', date: formatDate(myApp.value.interview_confirm_time || myApp.value.updated_at), type: 'danger' };
  }
  // 5. 面试已同意 (C端接受，等待录用)
  else if (s === '面试已同意') {
    if (index === 1) data = { title: '已投递', date: formatDate(myApp.value.created_at), type: 'success' };
    if (index === 2) data = { title: '已初筛', date: formatDate(myApp.value.invite_time), type: 'success' };
    if (index === 3) data = { title: '已面试', date: formatDate(myApp.value.interview_confirm_time), type: 'success' };
    if (index === 4) data = { title: '录用', status: '进行中', type: 'processing' };
  }
  // 6. 已录用 (B端录用，等完工)
  else if (s === '已录用') {
    if (index === 1) data = { title: '已投递', date: formatDate(myApp.value.created_at), type: 'success' };
    if (index === 2) data = { title: '已初筛', date: formatDate(myApp.value.invite_time), type: 'success' };
    if (index === 3) data = { title: '已面试', date: formatDate(myApp.value.interview_confirm_time), type: 'success' };
    if (index === 4) data = { title: '已录用', date: formatDate(myApp.value.hired_time), type: 'success' };
    if (index === 5) data = { title: '完工', status: '进行中', type: 'processing' };
  }
  // 7. 申请结单中 (C端申请完工)
  else if (s === '申请结单中') {
    if (index === 1) data = { title: '已投递', date: formatDate(myApp.value.created_at), type: 'success' };
    if (index === 2) data = { title: '已初筛', date: formatDate(myApp.value.invite_time), type: 'success' };
    if (index === 3) data = { title: '已面试', date: formatDate(myApp.value.interview_confirm_time), type: 'success' };
    if (index === 4) data = { title: '已录用', date: formatDate(myApp.value.hired_time), type: 'success' };
    if (index === 5) data = { title: '完工', status: '进行中', type: 'processing' };
  }
  // 8. 已完工 (结束)
  else if (s === '已完工') {
    if (index === 1) data = { title: '已投递', date: formatDate(myApp.value.created_at), type: 'success' };
    if (index === 2) data = { title: '已初筛', date: formatDate(myApp.value.invite_time), type: 'success' };
    if (index === 3) data = { title: '已面试', date: formatDate(myApp.value.interview_confirm_time), type: 'success' };
    if (index === 4) data = { title: '已录用', date: formatDate(myApp.value.hired_time), type: 'success' };
    if (index === 5) data = { title: '已完工', date: formatDate(myApp.value.finish_time), type: 'success' };
  }
  // 9. 结单争议
  else if (s === '结单争议') {
    if (index === 1) data = { title: '已投递', date: formatDate(myApp.value.created_at), type: 'success' };
    if (index === 2) data = { title: '已初筛', date: formatDate(myApp.value.invite_time), type: 'success' };
    if (index === 3) data = { title: '已面试', date: formatDate(myApp.value.interview_confirm_time), type: 'success' };
    if (index === 4) data = { title: '已录用', date: formatDate(myApp.value.hired_time), type: 'success' };
    if (index === 5) data = { title: '完工', status: '争议中', date: formatDate(myApp.value.finish_time), type: 'danger' };
  }

  return data;
}

const getLineData = (lineIndex) => {
  const n2 = getNodeData(lineIndex + 1).type;
  if (n2 === 'success') return 'success';
  if (n2 === 'processing') return 'processing';
  if (n2 === 'danger') return 'danger';
  return 'wait';
}

const callPhone = () => { window.location.href = `tel:${phone.value}` }

const apply = async () => {
  try {
    const res = await api.post(`/jobs/apply/${job.value.id}`)
    window.$toast(res.message || '投递成功')
    loadDetail()
  } catch (err) { window.$toast(err.response?.data?.detail || '投递失败') }
}

onMounted(() => { loadDetail() })
</script>

<style scoped>
/* 基础样式 */
.detail-page { min-height: 100vh; background: #f5f6f8; padding-bottom: 80px; }
.nav-bar { display: flex; align-items: center; gap: 8px; padding: 12px 16px; background: #fff; position: sticky; top: 0; z-index: 100; border-bottom: 1px solid #f3f4f6; font-size: 16px; font-weight: bold; color: #1f2937; }
.btn-back { cursor: pointer; display: flex; align-items: center; margin-left: -8px; }
.header-card { background: #fff; padding: 20px 16px; margin-bottom: 12px; }
.title-row { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.title-row h2 { font-size: 20px; color: #1f2937; flex: 1; }
.title-row .price { font-size: 18px; color: #ef4444; font-weight: bold; margin-left: 10px; }
.tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.tags span { font-size: 12px; padding: 4px 8px; background: #eff6ff; color: #2563eb; border-radius: 4px; }
.primary-tag { background: #2563eb !important; color: #fff !important; font-weight: bold; }
.loc { font-size: 14px; color: #4b5563; }
.section-card { background: #fff; padding: 20px 16px; margin-bottom: 12px; }
.section-card h3 { font-size: 16px; color: #1f2937; margin-bottom: 12px; font-weight: bold; }
.text-content { font-size: 14px; color: #4b5563; line-height: 1.6; white-space: pre-wrap; }

/* 时间轴 */
.timeline { display: flex; align-items: flex-start; justify-content: space-between; margin-top: 16px; padding: 0 5px; }
.tl-node { display: flex; flex-direction: column; align-items: center; position: relative; z-index: 2; width: 50px; flex-shrink: 0; text-align: center; }
.tl-node .dot { width: 12px; height: 12px; border-radius: 50%; border: 2px solid #fff; transition: all 0.3s; margin-bottom: 6px; }

/* 三行文字排版 */
.tl-node .text { font-size: 12px; font-weight: 500; white-space: nowrap; margin-bottom: 2px; }
.tl-node .status-text { font-size: 10px; white-space: nowrap; margin-bottom: 2px; font-weight: bold; }
.tl-node .date { font-size: 10px; color: #9ca3af; white-space: nowrap; }

/* 四色节点 */
.tl-node.success .dot { background: #2563eb; box-shadow: 0 0 0 1px #2563eb; }
.tl-node.success .text { color: #2563eb; }

.tl-node.processing .dot { background: #10b981; box-shadow: 0 0 0 1px #10b981; }
.tl-node.processing .text { color: #10b981; font-weight: bold; }
.tl-node.processing .status-text { color: #10b981; }

.tl-node.danger .dot { background: #ef4444; box-shadow: 0 0 0 1px #ef4444; }
.tl-node.danger .text { color: #ef4444; }
.tl-node.danger .status-text { color: #ef4444; }

.tl-node.wait .dot { background: #e5e7eb; box-shadow: 0 0 0 1px #e5e7eb; }
.tl-node.wait .text { color: #9ca3af; }

.tl-line { flex: 1; height: 2px; position: relative; top: 6px; z-index: 1; transition: all 0.3s; background: #e5e7eb; }
.tl-line.success { background: #2563eb; }
.tl-line.processing { background: #10b981; }
.tl-line.danger { background: #ef4444; }
.tl-line.wait { background: #e5e7eb; }

.bottom-bar { position: fixed; bottom: 0; left: 0; right: 0; height: 70px; background: #fff; display: flex; padding: 10px 16px; box-shadow: 0 -2px 10px rgba(0,0,0,0.05); padding-bottom: env(safe-area-inset-bottom); z-index: 999; }
.btn-call { flex: 1; background: #eff6ff; color: #2563eb; font-size: 16px; font-weight: bold; border-radius: 8px; margin-right: 12px; border: 1px solid #bfdbfe; }
.btn-apply { flex: 2; background: #2563eb; color: #fff; font-size: 16px; font-weight: bold; border-radius: 8px; border: none; }
</style>