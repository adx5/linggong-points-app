<!-- frontend/src/views/worker/JobDetail.vue (C端详情：引入进度条组件) -->
<template>
  <div class="detail-page" v-if="job.id">
    <div class="nav-bar">
      <div class="btn-back" @click="$router.back()">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#1f2937" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
      </div>
      <span class="nav-title">高薪急聘</span>
      <span class="nav-tag">名企直招</span>
    </div>

    <div class="header-card">
      <div class="title-row">
        <h2>{{ job.title }}</h2>
        <span class="price">{{ job.salary }}</span>
      </div>
      <div class="tags">
        <span class="primary-tag">{{ job.filter_tag }}</span>
        <span v-for="tag in (job.tags || '').split(',')" :key="tag">{{ tag }}</span>
      </div>
      <p class="loc">📍 {{ job.location }}</p>
    </div>

    <div class="section-card company-card" v-if="company.company_name">
      <div class="company-header">
        <div class="company-avatar">{{ company.company_name.charAt(0) }}</div>
        <div class="company-info">
          <h3>{{ company.company_name }}</h3>
          <p>企业直招 · 资质已认证</p>
        </div>
      </div>
      <p class="company-intro">{{ company.intro || '这家企业很低调，暂无简介。' }}</p>
    </div>

    <!-- 🚨 修复：引入进度条组件 -->
    <div class="section-card" v-if="myApp.id">
      <h3>我的应聘进度</h3>
      <OrderTimeline :app="myApp" />
    </div>

    <div class="section-card">
      <h3>人员要求</h3>
      <p class="text-content">{{ job.requirement || '暂无特殊要求' }}</p>
      <h3 style="margin-top: 15px;">岗位介绍</h3>
      <p class="text-content">{{ job.description || '暂无介绍' }}</p>
    </div>

    <div class="bottom-bar">
      <div class="action-icons">
        <div class="icon-btn" @click="toggleFavorite">
          <span class="icon">{{ isFavorite ? '⭐' : '☆' }}</span>
          <span>收藏</span>
        </div>
        <div class="icon-btn" @click="shareJob">
          <span class="icon">🔗</span>
          <span>分享</span>
        </div>
        <div class="icon-btn" @click="reportJob">
          <span class="icon">🚨</span>
          <span>举报</span>
        </div>
      </div>
      <div class="action-btns">
        <button class="btn-call" @click="callPhone">电话咨询</button>
        <button class="btn-apply" disabled v-if="myApp.status === '不合适' || myApp.status === '面试已拒绝'" style="background: #9ca3af;">流程已结束</button>
        <button class="btn-apply" disabled v-else-if="myApp.id" style="background: #10b981; color: white;">已投递</button>
        <button class="btn-apply" @click="openResumeSelect" v-else>立即投递</button>
      </div>
    </div>

    <div v-if="showResumeModal" class="modal-overlay" @click.self="showResumeModal = false">
      <div class="modal-content">
        <h3>选择投递的简历</h3>
        <p class="sub-tips">请选择一份最适合当前岗位的简历进行投递</p>
        <div class="resume-list">
          <div class="resume-item" v-for="res in userResumes" :key="res.id" @click="submitApply(res.id)">
            <h4>{{ res.target_job }}</h4>
            <p>📍 {{ res.target_city || '不限地点' }}</p>
          </div>
          <div v-if="userResumes.length === 0" class="empty">
            您还没有填写简历，请先前往“我的-简历维护”创建。
          </div>
        </div>
        <button class="btn-cancel" @click="showResumeModal = false">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api'
import OrderTimeline from '../../components/OrderTimeline.vue' // 🚨 引入组件

const route = useRoute()
const router = useRouter()
const job = ref({})
const company = ref({})
const myApp = ref({})

const isFavorite = ref(false)
const showResumeModal = ref(false)
const userResumes = ref([])

const loadDetail = async () => {
  try {
    const res = await api.get(`/jobs/${route.params.id}`)
    job.value = res.data.job
    company.value = res.data.company

    if (localStorage.getItem('token')) {
      const appRes = await api.get('/jobs/my-applications')
      const currentApp = appRes.data.find(a => a.job_id === job.value.id)
      if (currentApp) {
        myApp.value = currentApp
      }
    }
  } catch (err) { console.error(err) }
}

const callPhone = () => { window.location.href = `tel:13800000000` }
const toggleFavorite = () => { isFavorite.value = !isFavorite.value; window.$toast(isFavorite.value ? '已加入收藏' : '已取消收藏') }
const shareJob = () => window.$toast('正在生成分享海报...')
const reportJob = () => window.$toast('举报工单已提交，平台将介入核实')

const openResumeSelect = async () => {
  if (!localStorage.getItem('token')) {
    window.$toast('请先登录')
    window.location.hash = '#/login'
    return
  }
  try {
    const res = await api.get('/user/resume')
    const data = res.data
    if (!data.jobs || data.jobs.length === 0) {
      window.$toast('请先在“我的-简历维护”中创建一份岗位简历')
      setTimeout(() => { router.push('/worker/resume') }, 1000)
      return
    }
    userResumes.value = data.jobs
    showResumeModal.value = true
  } catch (err) { window.$toast('获取简历失败') }
}

const submitApply = async (resumeId) => {
  try {
    const res = await api.post(`/jobs/apply/${job.value.id}`, { resume_id: resumeId })
    window.$toast(res.message || '投递成功')
    showResumeModal.value = false
    loadDetail()
  } catch (err) { window.$toast(err.response?.data?.detail || '投递失败') }
}

onMounted(() => { loadDetail() })
</script>

<style scoped>
/* 样式保持原样，不用动 */
.detail-page { min-height: 100vh; background: #f5f6f8; padding-bottom: 90px; }
.nav-bar { display: flex; align-items: center; gap: 8px; padding: 12px 16px; background: #fff; position: sticky; top: 0; z-index: 100; border-bottom: 1px solid #f3f4f6; }
.btn-back { cursor: pointer; display: flex; align-items: center; margin-left: -8px; }
.nav-title { font-size: 16px; font-weight: bold; color: #1f2937; }
.nav-tag { background: #fef2f2; color: #ef4444; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: bold; margin-left: 8px;}
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
.company-card { display: flex; flex-direction: column; gap: 12px; }
.company-header { display: flex; align-items: center; gap: 12px; }
.company-avatar { width: 44px; height: 44px; background: #eff6ff; color: #2563eb; border-radius: 8px; display: flex; justify-content: center; align-items: center; font-size: 20px; font-weight: bold; }
.company-info h3 { margin: 0 0 4px 0; font-size: 16px; }
.company-info p { margin: 0; font-size: 12px; color: #10b981; background: #ecfdf5; display: inline-block; padding: 2px 6px; border-radius: 4px; }
.company-intro { font-size: 13px; color: #6b7280; background: #f9fafb; padding: 12px; border-radius: 8px; margin: 0; line-height: 1.5; }
.bottom-bar { position: fixed; bottom: 0; left: 0; right: 0; height: 70px; background: #fff; display: flex; align-items: center; padding: 10px 16px; box-shadow: 0 -2px 10px rgba(0,0,0,0.05); padding-bottom: env(safe-area-inset-bottom); z-index: 999; }
.action-icons { display: flex; gap: 16px; margin-right: 16px; }
.icon-btn { display: flex; flex-direction: column; align-items: center; font-size: 10px; color: #6b7280; cursor: pointer; }
.icon-btn .icon { font-size: 20px; margin-bottom: 2px; }
.action-btns { flex: 1; display: flex; gap: 10px; }
.btn-call { flex: 1; background: #eff6ff; color: #2563eb; font-size: 15px; font-weight: bold; border-radius: 8px; border: 1px solid #bfdbfe; cursor: pointer; }
.btn-apply { flex: 2; background: #2563eb; color: #fff; font-size: 15px; font-weight: bold; border-radius: 8px; border: none; cursor: pointer; }
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; justify-content: center; align-items: flex-end; }
.modal-content { background: #fff; width: 100%; border-radius: 16px 16px 0 0; padding: 20px; padding-bottom: env(safe-area-inset-bottom); }
.modal-content h3 { text-align: center; margin-bottom: 8px; font-size: 18px; }
.sub-tips { text-align: center; font-size: 12px; color: #9ca3af; margin-bottom: 16px; }
.resume-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px; max-height: 40vh; overflow-y: auto; }
.resume-item { border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; cursor: pointer; background: #f9fafb; }
.resume-item:active { border-color: #2563eb; background: #eff6ff; }
.resume-item h4 { font-size: 15px; color: #1f2937; margin-bottom: 4px; }
.resume-item p { font-size: 13px; color: #6b7280; margin: 0; }
.btn-cancel { width: 100%; background: #f3f4f6; color: #666; padding: 12px; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; }
</style>