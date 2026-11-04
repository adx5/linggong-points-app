<!-- frontend/src/views/worker/WorkerResume.vue (C端简历维护：修复弹窗层级与保存死锁) -->
<template>
  <div class="resume-page">
    <div class="sticky-header">
      <div class="header-left">
        <div class="btn-back" @click="$router.back()">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#1f2937" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
        </div>
        <h2>简历维护</h2>
      </div>
      <!-- 保存全部按钮 -->
      <span class="btn-save-text" @click="saveAllResume" :disabled="saving">
        {{ saving ? '保存中...' : '保存全部' }}
      </span>
    </div>

    <div class="content">
      <!-- 1. 通用基本信息区 -->
      <div class="form-card">
        <h3 class="section-title">基础信息（通用）</h3>
        <p class="tips-text">这部分信息只需填写一次，投递所有岗位时通用。</p>

        <div class="row-group">
          <input v-model="basicInfo.name" placeholder="姓名 (必填)" />
          <input v-model="basicInfo.phone" placeholder="手机号" type="tel" maxlength="11" />
        </div>
        <input v-model="basicInfo.email" placeholder="邮箱" type="email" style="margin-top: 10px;"/>

        <textarea v-model="basicInfo.skills" placeholder="核心技能 (如: Excel精通 | 叉车证 | 打字60字/分)" rows="2" style="margin-top: 10px;"></textarea>
        <textarea v-model="basicInfo.education" placeholder="教育背景 (如: 郑州大学 | 行政管理 | 大专 | 2020.09-2023.06)" rows="2" style="margin-top: 10px;"></textarea>
      </div>

      <!-- 2. 岗位专属简历区 -->
      <div class="jobs-section">
        <div class="section-header">
          <h3 class="section-title">我的岗位简历</h3>
          <button class="btn-add-job" @click="openEditModal(null)">+ 新增岗位简历</button>
        </div>
        <p class="tips-text">您可以为不同类别的岗位分别撰写不同的工作经历。</p>

        <div v-if="jobResumes.length === 0" class="empty-state">
          暂无岗位专属简历，请点击上方按钮新增。
        </div>

        <div class="job-resume-card" v-for="(job, index) in jobResumes" :key="job.id">
          <div class="card-header">
            <h4>{{ job.target_job || '未命名岗位' }}</h4>
            <div class="actions">
              <span class="btn-edit" @click="openEditModal(index)">编辑</span>
              <span class="btn-del" @click="deleteJobResume(index)">删除</span>
            </div>
          </div>
          <p class="job-loc">📍 意向地点：{{ job.target_city || '不限' }}</p>
          <p class="job-desc">工作经历：{{ job.work_experience ? job.work_experience.substring(0, 30) + '...' : '暂无' }}</p>
        </div>
      </div>

      <div class="bottom-spacer"></div>
    </div>

    <!-- 🚨 核心修复 1：提高弹窗 z-index，并固定底部提交按钮 -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-content edit-modal">
        <div class="modal-header">
          <h3>{{ editIndex === null ? '新增岗位简历' : '编辑岗位简历' }}</h3>
          <span class="btn-close" @click="showModal = false">✕</span>
        </div>
        <div class="modal-body">
          <div class="form-item">
            <label>求职意向岗位 (必填)</label>
            <input v-model="editForm.target_job" placeholder="如: 物流仓库理货员、行政专员" />
          </div>
          <div class="form-item">
            <label>意向城市/区域</label>
            <input v-model="editForm.target_city" placeholder="如: 郑州市 二七区" />
          </div>
          <div class="form-item">
            <label>工作 / 项目经历 (重点按STAR法则写)</label>
            <textarea v-model="editForm.work_experience" rows="5" placeholder="公司名称 | 岗位 | 起止时间&#10;· 负责XXX工作，通过XXX方法，达成XXX结果（量化，如：日均处理500件，零差错）。"></textarea>
          </div>
          <div class="form-item">
            <label>自我评价 (50-80字，突出与岗位匹配的优势)</label>
            <textarea v-model="editForm.self_evaluation" rows="3" placeholder="本人身体健康，能吃苦耐劳..."></textarea>
          </div>
        </div>
        <!-- 固定在弹窗底部的按钮 -->
        <div class="modal-footer">
          <button class="btn-confirm" @click="confirmEdit">确认保存此岗位简历</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()
const saving = ref(false)

// 数据模型
const basicInfo = reactive({
  name: '', phone: '', email: '', skills: '', education: ''
})
const jobResumes = ref([])

// 弹窗控制
const showModal = ref(false)
const editIndex = ref(null)
const editForm = reactive({
  id: '', target_job: '', target_city: '', work_experience: '', self_evaluation: ''
})

onMounted(async () => {
  try {
    const res = await api.get('/user/resume')
    if (res.data) {
      if (res.data.basic) Object.assign(basicInfo, res.data.basic)
      if (res.data.jobs) jobResumes.value = res.data.jobs
    }
    const userStr = localStorage.getItem('user')
    if (userStr && !basicInfo.phone) {
      const u = JSON.parse(userStr)
      if(u.phone) basicInfo.phone = u.phone
    }
  } catch (err) {
    console.error('获取简历失败', err)
  }
})

const openEditModal = (index) => {
  editIndex.value = index
  if (index === null) {
    Object.assign(editForm, {
      id: `job_${Date.now()}`,
      target_job: '', target_city: '', work_experience: '', self_evaluation: ''
    })
  } else {
    Object.assign(editForm, jobResumes.value[index])
  }
  showModal.value = true
}

const confirmEdit = () => {
  if (!editForm.target_job) return window.$toast('请填写求职意向岗位')

  if (editIndex.value === null) {
    jobResumes.value.push({ ...editForm })
  } else {
    jobResumes.value[editIndex.value] = { ...editForm }
  }
  showModal.value = false
  window.$toast('岗位简历已添加，请点击右上角保存全部')
}

const deleteJobResume = (index) => {
  if (window.confirm('确认删除这份岗位简历吗？')) {
    jobResumes.value.splice(index, 1)
  }
}

// 🚨 核心修复 2：放宽保存拦截，允许只保存基本信息
const saveAllResume = async () => {
  if (!basicInfo.name || !basicInfo.phone) {
    return window.$toast('请至少填写基础信息中的姓名和手机号')
  }

  saving.value = true
  try {
    await api.put('/user/resume', {
      basic: basicInfo,
      jobs: jobResumes.value
    })

    if (jobResumes.value.length === 0) {
      window.$toast('基础信息已保存。建议新增一份岗位简历以便投递。')
    } else {
      window.$toast('全部简历保存成功')
    }

    setTimeout(() => { router.back() }, 1000)
  } catch (err) {
    window.$toast('保存失败，请检查网络')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
/* 原有样式不变 */
.resume-page { min-height: 100vh; background: #f5f6f8; }
.sticky-header { position: sticky; top: 0; z-index: 99; background: #fff; padding: 16px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
.header-left { display: flex; align-items: center; gap: 8px; }
.btn-back { cursor: pointer; display: flex; align-items: center; margin-left: -8px; }
.sticky-header h2 { font-size: 18px; color: #1f2937; font-weight: bold; }
.btn-save-text { font-size: 14px; color: #10b981; font-weight: bold; cursor: pointer; }
.content { padding: 16px; }
.form-card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
.tips-text { font-size: 12px; color: #9ca3af; margin-bottom: 12px; }
.section-title { font-size: 15px; font-weight: bold; color: #1f2937; padding-left: 8px; border-left: 3px solid #2563eb; margin-bottom: 8px; }
.row-group { display: flex; gap: 10px; }
.row-group input { flex: 1; }
input, textarea { width: 100%; padding: 12px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; outline: none; background: #f9fafb; font-family: inherit; }
input:focus, textarea:focus { border-color: #2563eb; background: #fff; }
textarea { resize: vertical; }
.jobs-section { background: #fff; border-radius: 12px; padding: 16px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.btn-add-job { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: bold; cursor: pointer; }
.job-resume-card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; margin-top: 12px; background: #f9fafb; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.card-header h4 { font-size: 15px; color: #1f2937; margin: 0; }
.actions span { font-size: 12px; cursor: pointer; margin-left: 10px; }
.btn-edit { color: #2563eb; }
.btn-del { color: #ef4444; }
.job-loc { font-size: 12px; color: #6b7280; margin-bottom: 6px; }
.job-desc { font-size: 13px; color: #4b5563; line-height: 1.4; }
.empty-state { text-align: center; color: #9ca3af; font-size: 13px; padding: 20px 0; }

/* 🚨 核心修复：弹窗样式重写 */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6);
  z-index: 9999; /* 层级调至最高，盖住底部导航栏 */
  display: flex;
  justify-content: center;
  align-items: flex-end;
}
.edit-modal {
  background: #fff;
  width: 100%;
  height: 85vh; /* 高度占屏幕85% */
  border-radius: 16px 16px 0 0;
  display: flex;
  flex-direction: column; /* 使用 Flex 布局固定头部和底部 */
}
.modal-header {
  padding: 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}
.modal-header h3 { font-size: 16px; font-weight: bold; margin: 0; }
.btn-close { cursor: pointer; font-size: 18px; color: #999; }
.modal-body {
  padding: 16px;
  overflow-y: auto; /* 中间内容可滚动 */
  flex: 1;
}
.form-item { margin-bottom: 16px; }
.form-item label { display: block; font-size: 14px; font-weight: bold; color: #333; margin-bottom: 8px; }
.modal-footer {
  padding: 12px 16px;
  border-top: 1px solid #eee;
  padding-bottom: env(safe-area-inset-bottom);
  flex-shrink: 0;
  background: #fff;
}
.btn-confirm { width: 100%; background: #2563eb; color: #fff; padding: 14px; border-radius: 8px; font-size: 16px; font-weight: bold; border: none; cursor: pointer; }
</style>