<!-- (B端简历库：收到简历 极简待办 + 全部简历 台账) -->
<template>
  <div class="talent-page">
    <div class="sticky-header">
      <h2>简历库</h2>
    </div>

    <!-- 顶部一级 Tab -->
    <div class="main-tabs">
      <div class="m-tab" :class="{ active: mainTab === 'inbox' }" @click="mainTab = 'inbox'">
        收到简历 <span class="badge" v-if="inboxCount > 0">{{ inboxCount }}</span>
      </div>
      <div class="m-tab" :class="{ active: mainTab === 'all' }" @click="mainTab = 'all'">全部简历</div>
    </div>

    <!-- Tab 1：收到简历 (极简待办) -->
    <div v-if="mainTab === 'inbox'" class="list-content">
      <div class="card" v-for="item in inboxList" :key="item.id" @click="openDetail(item)">
        <div class="row">
          <div class="user">
            <h3>{{ item.worker_name }}</h3>
            <p class="job-title">投递: {{ item.job_title }}</p>
          </div>
        </div>
        <div class="actions">
          <button class="btn-reject" @click.stop="openRejectModal(item)">不合适</button>
          <button class="btn-pass" @click.stop="openInvite(item)">邀面试</button>
        </div>
      </div>
      <div v-if="inboxList.length === 0" class="empty">
        <p>🎉 今日待办已处理完毕，干得漂亮！</p>
      </div>
    </div>

    <!-- Tab 2：全部简历 (数据台账) -->
    <div v-if="mainTab === 'all'" class="list-content">
      <!-- 筛选工具栏 -->
      <div class="filter-bar">
        <div class="chips">
          <span :class="{ active: filterStatus === 'all' }" @click="filterStatus = 'all'">全部</span>
          <span :class="{ active: filterStatus === '1' }" @click="filterStatus = '1'">待处理</span>
          <span :class="{ active: filterStatus === '3' }" @click="filterStatus = '3'">面试中</span>
          <span :class="{ active: filterStatus === '5' }" @click="filterStatus = '5'">已录用</span>
          <span :class="{ active: filterStatus === '8' }" @click="filterStatus = '8'">已完工</span>
        </div>
        <div class="checkbox-wrap">
          <input type="checkbox" id="showRejected" v-model="showRejected">
          <label for="showRejected">包含已淘汰</label>
        </div>
      </div>

      <div class="card" v-for="item in allList" :key="item.id" @click="openDetail(item)">
        <div class="row">
          <div class="user">
            <h3>{{ item.worker_name }}</h3>
            <p class="job-title">投递: {{ item.job_title }}</p>
          </div>
          <div class="status-badge" :class="getStatusClass(item.status)">
            {{ getStatusText(item.status) }}
          </div>
        </div>
      </div>
      <div v-if="allList.length === 0" class="empty">暂无匹配的简历</div>
    </div>

    <!-- 详情弹窗 (展示脱敏手机号) -->
    <div v-if="showDetail" class="modal-overlay" @click.self="showDetail = false">
      <div class="modal-content">
        <h3>人才档案详情</h3>
        <div class="detail-info">
          <p><strong>姓名：</strong>{{ currentResume.worker_name }}</p>
          <p><strong>电话：</strong>{{ maskPhone(currentResume.worker_phone) }}</p>
        </div>
        <div class="modal-btns">
          <button class="btn-call" @click="call(currentResume.worker_phone)">📞 拨打电话</button>
          <button class="btn-close" @click="showDetail = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- 邀面试弹窗 -->
    <div v-if="showInviteModal" class="modal-overlay" @click.self="showInviteModal = false">
      <div class="modal-content">
        <h3>发起面试邀请</h3>
        <div class="form-item"><label>面试时间</label><input type="datetime-local" v-model="inviteForm.time" /></div>
        <div class="form-item"><label>面试地点</label><input type="text" v-model="inviteForm.address" placeholder="如：XX厂区人事部" /></div>
        <div class="form-item">
          <label>面试方式</label>
          <select v-model="inviteForm.method"><option value="线下">线下实地</option><option value="线上">线上视频</option></select>
        </div>
        <div class="btn-group">
          <button class="btn-cancel" @click="showInviteModal = false">取消</button>
          <button class="btn-pass" @click="submitInvite">发送邀请</button>
        </div>
      </div>
    </div>

    <!-- 拒绝问卷 -->
    <div v-if="showRejectModal" class="modal-overlay" @click.self="showRejectModal = false">
      <div class="modal-content">
        <h3>不合适原因</h3>
        <div class="form-item">
          <select v-model="rejectForm.mainReason">
            <option value="">请选择原因...</option>
            <option value="经验或技能不匹配">经验或技能不匹配</option>
            <option value="薪资或距离期望不符">薪资或距离期望不符</option>
            <option value="沟通态度不佳">沟通态度不佳</option>
            <option value="岗位已招满">岗位已招满</option>
          </select>
        </div>
        <div class="form-item"><textarea v-model="rejectForm.detail" placeholder="补充说明..." rows="2"></textarea></div>
        <div class="btn-group">
          <button class="btn-cancel" @click="showRejectModal = false">取消</button>
          <button class="btn-pass" @click="submitReject">确认提交</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api'

const mainTab = ref('inbox')
const allData = ref([])
const filterStatus = ref('all')
const showRejected = ref(false)

// 弹窗控制
const showDetail = ref(false)
const currentResume = ref({})
const showInviteModal = ref(false)
const inviteForm = ref({ time: '', address: '', method: '线下' })
const showRejectModal = ref(false)
const rejectForm = ref({ mainReason: '', detail: '' })

const loadData = async () => {
  const res = await api.get('/jobs/received')
  allData.value = res.data || []
}

// Tab 1 数据：仅状态 1 (待处理)
const inboxList = computed(() => {
  return allData.value.filter(item => item.status === 1)
})
const inboxCount = computed(() => inboxList.value.length)

// Tab 2 数据：受 Chip 和 Checkbox 控制
const allList = computed(() => {
  return allData.value.filter(item => {
    if (!showRejected.value && [4, 6].includes(item.status)) return false
    if (filterStatus.value !== 'all' && item.status.toString() !== filterStatus.value) return false
    return true
  })
})

// 🚨 手机号脱敏方法
const maskPhone = (phone) => {
  if (!phone) return ''
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

const getStatusText = (status) => {
  const map = { 1: '待处理', 2: '待面试', 3: '面试已同意', 4: '面试已拒绝', 5: '已录用', 6: '不合适', 7: '申请结单中', 8: '已完工', 9: '结单争议' }
  return map[status] || '未知'
}
const getStatusClass = (status) => {
  if ([1].includes(status)) return 'pending'
  if ([5, 8].includes(status)) return 'success'
  if ([2, 3, 7].includes(status)) return 'warning'
  return 'danger'
}

// 业务操作
const openDetail = (item) => { currentResume.value = item; showDetail.value = true }
const call = (phone) => { window.location.href = `tel:${phone}` }

const openInvite = (item) => {
  currentResume.value = item;
  inviteForm.value = { time: '', address: '', method: '线下' };
  showInviteModal.value = true
}

const submitInvite = async () => {
  if (!inviteForm.value.time || !inviteForm.value.address) return window.$toast('请填写时间地点')
  try {
    await api.post('/jobs/interview/invite', {
      application_id: currentResume.value.id,
      time: inviteForm.value.time,
      address: inviteForm.value.address,
      method: inviteForm.value.method
    })
    window.$toast('面试邀请已发送')
    showInviteModal.value = false
    loadData()
  } catch (err) { window.$toast('发送失败') }
}

const openRejectModal = (item) => { currentResume.value = item; rejectForm.value = { mainReason: '', detail: '' }; showRejectModal.value = true }

const submitReject = async () => {
  if (!rejectForm.value.mainReason) return window.$toast('请选择原因')
  const reason = rejectForm.value.detail ? `${rejectForm.value.mainReason}(${rejectForm.value.detail})` : rejectForm.value.mainReason
  await api.put(`/jobs/application/${currentResume.value.id}?status=6&reason=${encodeURIComponent(reason)}`)
  window.$toast('操作成功'); showRejectModal.value = false; loadData()
}

onMounted(() => { loadData() })
</script>

<style scoped>
/* 样式保持上一版不变 */
.talent-page { min-height: 100vh; background: #f0f2f5; }
.sticky-header { position: sticky; top: 0; z-index: 99; background: #fff; padding: 16px; border-bottom: 1px solid #eee; }
.sticky-header h2 { font-size: 18px; color: #1f2937; }

.main-tabs { display: flex; background: #fff; border-bottom: 1px solid #eee; }
.m-tab { flex: 1; text-align: center; padding: 14px 0; font-size: 15px; color: #666; cursor: pointer; font-weight: bold; position: relative; }
.m-tab.active { color: #2563eb; border-bottom: 2px solid #2563eb; }
.m-tab .badge { background: #ef4444; color: #fff; font-size: 11px; padding: 2px 6px; border-radius: 10px; margin-left: 4px; }

.list-content { padding: 16px; }
.card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; cursor: pointer; }
.row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.user h3 { font-size: 16px; color: #1f2937; margin-bottom: 6px; }
.job-title { font-size: 13px; color: #9ca3af; }
.actions { display: flex; gap: 12px; }
.actions button { flex: 1; padding: 10px; border-radius: 6px; font-weight: bold; border: none; font-size: 14px; cursor: pointer; }
.btn-reject { background: #fef2f2; color: #ef4444; border: 1px solid #fecaca !important; }
.btn-pass { background: #2563eb; color: #fff; }

.filter-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.chips { display: flex; gap: 8px; overflow-x: auto; flex: 1; padding-right: 10px; }
.chips::-webkit-scrollbar { display: none; }
.chips span { white-space: nowrap; padding: 6px 14px; background: #fff; border-radius: 16px; font-size: 13px; color: #666; cursor: pointer; transition: all 0.2s; }
.chips span.active { background: #2563eb; color: #fff; font-weight: bold; }
.checkbox-wrap { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #666; white-space: nowrap; }

.status-badge { font-size: 13px; font-weight: bold; }
.status-badge.pending { color: #f59e0b; }
.status-badge.success { color: #10b981; }
.status-badge.warning { color: #2563eb; }
.status-badge.danger { color: #ef4444; }

.empty { text-align: center; padding: 60px 0; color: #9ca3af; }

/* 弹窗样式 */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 999; display: flex; justify-content: center; align-items: center; }
.modal-content { background: #fff; width: 85%; border-radius: 12px; padding: 20px; }
.modal-content h3 { text-align: center; margin-bottom: 20px; font-size: 18px; }
.detail-info p { font-size: 14px; color: #333; margin-bottom: 10px; }
.modal-btns { display: flex; gap: 10px; margin-top: 20px; }
.modal-btns button { flex: 1; padding: 12px; border-radius: 6px; font-weight: bold; border: none; cursor: pointer; }
.btn-call { background: #eff6ff; color: #2563eb; }
.btn-close { background: #f3f4f6; color: #666; }
.form-item { margin-bottom: 16px; }
.form-item label { display: block; font-size: 14px; font-weight: bold; margin-bottom: 8px; }
.form-item input, .form-item select, .form-item textarea { width: 100%; padding: 10px; border: 1px solid #e5e7eb; border-radius: 6px; outline: none; font-family: inherit; resize: none; }
.btn-group { display: flex; gap: 12px; margin-top: 20px; }
.btn-group button { flex: 1; padding: 12px; border-radius: 6px; font-weight: bold; border: none; }
.btn-cancel { background: #f3f4f6; color: #666; }
</style>