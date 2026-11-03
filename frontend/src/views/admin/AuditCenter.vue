<!-- (资质审核中心：恢复三个Tab，带驳回原因) -->
<template>
  <div class="audit-page">
    <div class="header">
      <h2>资质审核中心</h2>
      <p>合规准入 · 严守底线</p>
    </div>

    <div class="tabs">
      <div class="tab" :class="{ active: currentTab === 'company' }" @click="currentTab = 'company'">企业审核</div>
      <div class="tab" :class="{ active: currentTab === 'agent' }" @click="currentTab = 'agent'">经纪人审核</div>
      <div class="tab" :class="{ active: currentTab === 'provider' }" @click="currentTab = 'provider'">服务商审核</div>
    </div>

    <div class="list-content">
      <div class="card" v-for="item in filteredList" :key="item.id" @click="openDetail(item)">
        <div class="header-row">
          <h3>{{ item.name }}</h3>
          <span class="status" :class="item.status === 'active' ? 'pass' : (item.status === 'rejected' ? 'danger' : 'pending')">
            {{ item.status === 'active' ? '已通过' : (item.status === 'rejected' ? '已驳回' : '待审核') }}
          </span>
        </div>
        <div class="info-row"><span>档案号:</span> {{ item.file_no }}</div>
        <div class="info-row"><span>信用代码:</span> {{ item.ext_info?.credit_code || '未填写' }}</div>
        <div class="arrow-hint">点击调阅详细档案比对 ></div>
      </div>
      <div v-if="filteredList.length === 0" class="empty">当前分类暂无数据</div>
    </div>

    <!-- 详情弹窗 -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-content archive-modal">
        <div class="modal-header">
          <h3>{{ currentItem.name }}</h3>
          <span class="file-no">档案号：{{ currentItem.file_no }}</span>
        </div>
        <div class="modal-body">
          <div class="section-block bg-gray">
            <h4 class="section-title">私密资质备案</h4>
            <div class="img-placeholder">📄 营业执照 / 身份证 大图预览区</div>
            <div class="private-info">
              <p><span>联系人：</span>{{ currentItem.ext_info?.contact_name || '未填写' }}</p>
              <p><span>电话：</span>{{ currentItem.ext_info?.contact_phone || '未填写' }}</p>
              <p><span>信用代码：</span>{{ currentItem.ext_info?.credit_code || '未填写' }}</p>
              <p v-if="currentItem.status === 'rejected'" style="color:#ef4444;"><span>驳回原因：</span>{{ currentItem.reject_reason }}</p>
            </div>
          </div>
        </div>
        <div class="modal-footer" v-if="currentItem.status === 'pending'">
          <button class="btn-reject" @click="handleAudit(false)">驳回资质</button>
          <button class="btn-pass" @click="handleAudit(true)">比对无误，通过</button>
        </div>
        <div class="modal-footer" v-else>
          <button class="btn-close" @click="showModal = false">关闭档案</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../../api'

const currentTab = ref('company')
const allList = ref([])
const showModal = ref(false)
const currentItem = ref({})

const loadCompanies = async () => {
  try {
    const res = await api.get('/admin/companies')
    allList.value = res.data
  } catch (err) { window.$toast('获取审核列表失败') }
}

const filteredList = computed(() => {
  return allList.value.filter(item => {
    if (currentTab.value === 'company') return item.type === 'company' || !item.type
    if (currentTab.value === 'agent') return item.type === 'agent'
    if (currentTab.value === 'provider') return item.type === 'provider'
    return true
  })
})

const openDetail = (item) => {
  currentItem.value = item
  showModal.value = true
}

const handleAudit = async (pass) => {
  let rejectReason = ""
  if (!pass) {
    rejectReason = window.prompt('请填写驳回原因，将发送至 B 端：', '')
    if (rejectReason === null) return
    if (!rejectReason.trim()) return window.$toast('必须填写驳回原因')
  } else {
    const confirmName = window.prompt(`经核查比对无误。请输入企业名称【${currentItem.value.name}】确认录入：`, '')
    if (confirmName !== currentItem.value.name) return window.$toast('企业名称输入不一致，无法通过')
  }

  try {
    await api.post('/audit/verify', {
      entity_id: currentItem.value.id,
      pass_verify: pass,
      reject_reason: rejectReason
    })
    window.$toast('操作成功')
    showModal.value = false
    loadCompanies()
  } catch (err) { window.$toast('审核操作失败') }
}

onMounted(() => { loadCompanies() })
</script>

<style scoped>
.audit-page { min-height: 100vh; background: #f0f4f8; padding-bottom: 80px; }
.header { background: #0052d9; padding: 30px 20px 20px; color: #ffffff; }
.header h2 { font-size: 20px; margin-bottom: 4px; }
.header p { font-size: 13px; opacity: 0.8; }
.tabs { display: flex; background: #ffffff; border-bottom: 1px solid #e5e7eb; position: sticky; top: 0; z-index: 99; }
.tab { flex: 1; text-align: center; padding: 14px 0; font-size: 14px; color: #6b7280; cursor: pointer; font-weight: bold; }
.tab.active { color: #0052d9; border-bottom: 2px solid #0052d9; }
.list-content { padding: 16px; }
.card { background: #ffffff; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); cursor: pointer; }
.header-row { display: flex; justify-content: space-between; margin-bottom: 10px; }
.header-row h3 { font-size: 16px; color: #333333; }
.status { font-size: 12px; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
.status.pending { background: #fffbeb; color: #f59e0b; }
.status.pass { background: #ecfdf5; color: #10b981; }
.status.danger { background: #fef2f2; color: #ef4444; }
.info-row { font-size: 13px; color: #4b5563; margin-bottom: 6px; }
.info-row span { color: #9ca3af; }
.arrow-hint { text-align: right; font-size: 12px; color: #0052d9; margin-top: 8px; }
.empty { text-align: center; color: #9ca3af; padding: 40px; }
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); z-index: 999; display: flex; justify-content: center; align-items: center; }
.archive-modal { background: #f8fafc; width: 92%; border-radius: 12px; display: flex; flex-direction: column; max-height: 85vh; }
.modal-header { padding: 16px 20px; background: #ffffff; border-bottom: 1px solid #e5e7eb; border-radius: 12px 12px 0 0; display: flex; justify-content: space-between; align-items: flex-end; }
.modal-header h3 { font-size: 18px; color: #1f2937; }
.file-no { font-size: 12px; color: #6b7280; }
.modal-body { padding: 16px; overflow-y: auto; flex: 1; }
.section-block { background: #ffffff; border-radius: 8px; padding: 12px; margin-bottom: 12px; border: 1px solid #e5e7eb; }
.section-block.bg-gray { background: #f1f5f9; border-color: #cbd5e1; }
.section-title { font-size: 14px; color: #0052d9; margin-bottom: 10px; border-left: 3px solid #0052d9; padding-left: 8px; font-weight: bold; }
.private-info p { font-size: 13px; color: #374151; margin-bottom: 6px; }
.private-info span { color: #6b7280; }
.img-placeholder { height: 120px; background: #e2e8f0; display: flex; justify-content: center; align-items: center; color: #64748b; font-size: 13px; border-radius: 6px; border: 1px dashed #94a3b8; margin-bottom: 10px; }
.modal-footer { padding: 16px 20px; background: #ffffff; border-top: 1px solid #e5e7eb; border-radius: 0 0 12px 12px; display: flex; gap: 12px; }
.modal-footer button { flex: 1; padding: 12px; border-radius: 6px; font-weight: bold; border: none; cursor: pointer; font-size: 15px; }
.btn-reject { background: #fef2f2; color: #ef4444; border: 1px solid #fecaca; }
.btn-pass { background: #0052d9; color: #ffffff; }
.btn-close { background: #f3f4f6; color: #4b5563; border: 1px solid #e5e7eb; }
</style>