<!-- frontend/src/components/OrderTimeline.vue (全端通用：应聘进度时间轴) -->
<template>
  <div class="timeline">
    <div class="tl-node" :class="getNodeData(1).type">
      <div class="dot"></div>
      <div class="text">{{ getNodeData(1).title }}</div>
      <div class="status-text" v-if="getNodeData(1).statusText">{{ getNodeData(1).statusText }}</div>
      <div class="date" v-if="getNodeData(1).date">{{ getNodeData(1).date }}</div>
    </div>
    <div class="tl-line" :class="getLineData(1)"></div>

    <div class="tl-node" :class="getNodeData(2).type">
      <div class="dot"></div>
      <div class="text">{{ getNodeData(2).title }}</div>
      <div class="status-text" v-if="getNodeData(2).statusText">{{ getNodeData(2).statusText }}</div>
      <div class="date" v-if="getNodeData(2).date">{{ getNodeData(2).date }}</div>
    </div>
    <div class="tl-line" :class="getLineData(2)"></div>

    <div class="tl-node" :class="getNodeData(3).type">
      <div class="dot"></div>
      <div class="text">{{ getNodeData(3).title }}</div>
      <div class="status-text" v-if="getNodeData(3).statusText">{{ getNodeData(3).statusText }}</div>
      <div class="date" v-if="getNodeData(3).date">{{ getNodeData(3).date }}</div>
    </div>
    <div class="tl-line" :class="getLineData(3)"></div>

    <div class="tl-node" :class="getNodeData(4).type">
      <div class="dot"></div>
      <div class="text">{{ getNodeData(4).title }}</div>
      <div class="status-text" v-if="getNodeData(4).statusText">{{ getNodeData(4).statusText }}</div>
      <div class="date" v-if="getNodeData(4).date">{{ getNodeData(4).date }}</div>
    </div>
    <div class="tl-line" :class="getLineData(4)"></div>

    <div class="tl-node" :class="getNodeData(5).type">
      <div class="dot"></div>
      <div class="text">{{ getNodeData(5).title }}</div>
      <div class="status-text" v-if="getNodeData(5).statusText">{{ getNodeData(5).statusText }}</div>
      <div class="date" v-if="getNodeData(5).date">{{ getNodeData(5).date }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  app: { type: Object, required: true }
})

const formatDate = (dateTimeStr) => {
  if (!dateTimeStr) return ''
  return dateTimeStr.split(' ')[0]
}

// 兼容 C端返回的字符串状态和 B端返回的数字状态
const statusCode = computed(() => {
  const s = props.app.status
  if (typeof s === 'number') return s
  const map = {
    "待处理": 1, "待面试": 2, "面试已同意": 3, "面试已拒绝": 4,
    "已录用": 5, "不合适": 6, "申请结单中": 7, "已完工": 8, "结单争议": 9
  }
  return map[s] || 1
})

const getNodeData = (index) => {
  const s = statusCode.value
  let data = { title: '', statusText: '', date: '', type: 'wait' }
  const baseNames = ['已投递', '初筛', '面试', '录用', '完工']
  data.title = baseNames[index - 1]

  if (s === 1) {
    if (index === 1) data = { title: '已投递', date: formatDate(props.app.created_at), type: 'success' }
    if (index === 2) data = { title: '初筛', statusText: '进行中', type: 'processing' }
  } else if (s === 6) {
    if (index === 1) data = { title: '已投递', date: formatDate(props.app.created_at), type: 'success' }
    if (index === 2) data = { title: '初筛', statusText: '未通过', date: formatDate(props.app.updated_at || props.app.invite_time), type: 'danger' }
  } else if (s === 2) {
    if (index === 1) data = { title: '已投递', date: formatDate(props.app.created_at), type: 'success' }
    if (index === 2) data = { title: '已初筛', date: formatDate(props.app.invite_time), type: 'success' }
    if (index === 3) data = { title: '面试', statusText: '进行中', type: 'processing' }
  } else if (s === 4) {
    if (index === 1) data = { title: '已投递', date: formatDate(props.app.created_at), type: 'success' }
    if (index === 2) data = { title: '已初筛', date: formatDate(props.app.invite_time), type: 'success' }
    if (index === 3) data = { title: '面试', statusText: '已放弃', date: formatDate(props.app.interview_confirm_time), type: 'danger' }
  } else if (s === 3) {
    if (index === 1) data = { title: '已投递', date: formatDate(props.app.created_at), type: 'success' }
    if (index === 2) data = { title: '已初筛', date: formatDate(props.app.invite_time), type: 'success' }
    if (index === 3) data = { title: '已面试', date: formatDate(props.app.interview_confirm_time), type: 'success' }
    if (index === 4) data = { title: '录用', statusText: '进行中', type: 'processing' }
  } else if (s === 5) {
    if (index === 1) data = { title: '已投递', date: formatDate(props.app.created_at), type: 'success' }
    if (index === 2) data = { title: '已初筛', date: formatDate(props.app.invite_time), type: 'success' }
    if (index === 3) data = { title: '已面试', date: formatDate(props.app.interview_confirm_time), type: 'success' }
    if (index === 4) data = { title: '已录用', date: formatDate(props.app.hired_time), type: 'success' }
    if (index === 5) data = { title: '完工', statusText: '进行中', type: 'processing' }
  } else if (s === 7) {
    if (index === 1) data = { title: '已投递', date: formatDate(props.app.created_at), type: 'success' }
    if (index === 2) data = { title: '已初筛', date: formatDate(props.app.invite_time), type: 'success' }
    if (index === 3) data = { title: '已面试', date: formatDate(props.app.interview_confirm_time), type: 'success' }
    if (index === 4) data = { title: '已录用', date: formatDate(props.app.hired_time), type: 'success' }
    if (index === 5) data = { title: '完工', statusText: '确认中', type: 'processing' }
  } else if (s === 8) {
    if (index === 1) data = { title: '已投递', date: formatDate(props.app.created_at), type: 'success' }
    if (index === 2) data = { title: '已初筛', date: formatDate(props.app.invite_time), type: 'success' }
    if (index === 3) data = { title: '已面试', date: formatDate(props.app.interview_confirm_time), type: 'success' }
    if (index === 4) data = { title: '已录用', date: formatDate(props.app.hired_time), type: 'success' }
    if (index === 5) data = { title: '已完工', date: formatDate(props.app.finish_time), type: 'success' }
  } else if (s === 9) {
    if (index === 1) data = { title: '已投递', date: formatDate(props.app.created_at), type: 'success' }
    if (index === 2) data = { title: '已初筛', date: formatDate(props.app.invite_time), type: 'success' }
    if (index === 3) data = { title: '已面试', date: formatDate(props.app.interview_confirm_time), type: 'success' }
    if (index === 4) data = { title: '已录用', date: formatDate(props.app.hired_time), type: 'success' }
    if (index === 5) data = { title: '完工', statusText: '争议中', date: formatDate(props.app.finish_time), type: 'danger' }
  }

  return data
}

const getLineData = (lineIndex) => {
  const n2 = getNodeData(lineIndex + 1).type
  if (n2 === 'success') return 'success'
  if (n2 === 'processing') return 'processing'
  if (n2 === 'danger') return 'danger'
  return 'wait'
}
</script>

<style scoped>
.timeline { display: flex; align-items: flex-start; justify-content: space-between; margin-top: 16px; padding: 0 5px; }
.tl-node { display: flex; flex-direction: column; align-items: center; position: relative; z-index: 2; width: 50px; flex-shrink: 0; text-align: center; }
.tl-node .dot { width: 12px; height: 12px; border-radius: 50%; border: 2px solid #fff; transition: all 0.3s; margin-bottom: 6px; }
.tl-node .text { font-size: 12px; font-weight: 500; white-space: nowrap; margin-bottom: 2px; }
.tl-node .status-text { font-size: 10px; white-space: nowrap; margin-bottom: 2px; font-weight: bold; }
.tl-node .date { font-size: 10px; color: #9ca3af; white-space: nowrap; }

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
</style>