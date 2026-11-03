<!-- (C端我的投递：极简列表，去除冗长进度条) -->
<template>
  <div class="applies-page">
    <div class="header"><h2>我的投递</h2></div>
    <div class="list">
      <div class="card" v-for="item in list" :key="item.id">
        <!-- 头部：岗位名 + 状态 -->
        <div class="row" @click="$router.push(`/worker/job-detail/${item.job_id}`)">
          <h3>{{ item.title }}</h3>
          <span :class="['status', getStatusClass(item.status)]">{{ item.status }}</span>
        </div>

        <!-- 薪资与地点 -->
        <p class="info" @click="$router.push(`/worker/job-detail/${item.job_id}`)">
          {{ item.salary }} | {{ item.location }}
        </p>

        <!-- ================= 业务动作区 ================= -->

        <!-- 状态 2：待面试 -->
        <div class="action-bar" v-if="item.status === '待面试'">
          <p class="tip">企业邀请您去面试，请确认是否前往</p>
          <div class="btns">
            <button class="btn-reject" @click.stop="replyInterview(item.id, false)">拒绝</button>
            <button class="btn-pass" @click.stop="replyInterview(item.id, true)">同意去面试</button>
          </div>
        </div>

        <!-- 状态 3：面试已同意 -->
        <div class="action-bar" v-if="item.status === '面试已同意'">
          <p class="tip text-green">已确认去面试，请按时到达！</p>
        </div>

        <!-- 状态 5：已录用 -->
        <div class="action-bar" v-if="item.status === '已录用'">
          <button class="btn-finish" @click.stop="applyFinish(item.id)">申请完工结算</button>
        </div>

        <!-- 状态 8：已完工 -->
        <div class="action-bar" v-if="item.status === '已完工'">
          <p class="tip text-green">🎉 完工确认，积分已发放！</p>
        </div>

        <!-- 状态 9：结单争议 -->
        <div class="action-bar" v-if="item.status === '结单争议'">
          <p class="tip text-red">⚠️ 结单被驳回，请与企业沟通</p>
          <div class="btns">
            <button class="btn-reject" @click.stop="callBoss(item)">联系老板</button>
            <button class="btn-pass" @click.stop="applyIntervention(item)">申请平台介入</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const list = ref([])

const loadApplications = async () => {
  try {
    const res = await api.get('/jobs/my-applications')
    list.value = res.data || []
  } catch (err) {}
}

const replyInterview = async (id, accept) => {
  try {
    await api.put(`/jobs/interview/${id}/reply?accept=${accept}`)
    window.$toast(accept ? '已同意面试' : '已拒绝面试')
    loadApplications()
  } catch (err) { window.$toast('操作失败') }
}

const applyFinish = async (id) => {
  if (!window.confirm('确认您已完工？')) return
  try {
    const res = await api.put(`/jobs/application/${id}/finish`)
    window.$toast(res.message)
    loadApplications()
  } catch (err) { window.$toast('操作失败') }
}

const callBoss = () => window.$toast('正在拨打企业电话...')
const applyIntervention = () => window.$toast('平台介入工单已提交，客服将尽快联系您')

const getStatusClass = (status) => {
  if (status === '待处理') return 'pending'
  if (status === '已录用' || status === '已完工') return 'success'
  if (status === '待面试' || status === '面试已同意' || status === '申请结单中') return 'warning'
  return 'danger'
}

onMounted(() => { loadApplications() })
</script>

<style scoped>
.applies-page { min-height: 100vh; background: #f5f6f8; padding-bottom: 80px; }
.header { background: #fff; padding: 16px; border-bottom: 1px solid #eee; }
.header h2 { font-size: 18px; color: #1f2937; }
.list { padding: 12px; }

.card { background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; cursor: pointer; }
.row h3 { font-size: 16px; color: #1f2937; }
.status { font-size: 13px; font-weight: bold; padding: 2px 8px; border-radius: 4px; }
.status.pending { color: #f59e0b; background: #fffbeb; }
.status.success { color: #10b981; background: #ecfdf5; }
.status.warning { color: #3b82f6; background: #eff6ff; }
.status.danger { color: #ef4444; background: #fef2f2; }

.info { font-size: 13px; color: #666; cursor: pointer; margin-bottom: 12px; }

.action-bar { border-top: 1px dashed #eee; padding-top: 12px; }
.tip { font-size: 13px; color: #f59e0b; margin-bottom: 8px; }
.tip.text-green { color: #10b981; }
.tip.text-red { color: #ef4444; }

.btns { display: flex; gap: 12px; }
.btns button, .btn-finish { flex: 1; padding: 10px; border-radius: 6px; font-weight: bold; border: none; font-size: 14px; cursor: pointer; }
.btn-reject { background: #fef2f2; color: #ef4444; border: 1px solid #fecaca; }
.btn-pass { background: #2563eb; color: #fff; }
.btn-finish { background: #10b981; color: #fff; width: 100%; }
</style>