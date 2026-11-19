<!-- frontend/src/views/worker/WorkerResume.vue (大字版 P4 极简简历) -->
<template>
  <div class="resume-page">
    <header class="page-head">
      <button class="back-btn" type="button" aria-label="返回" @click="router.back()">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#111" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
      </button>
      <div class="head-text">
        <h1>我的简历</h1>
        <p>完善后投递成功率更高</p>
      </div>
    </header>

    <!-- 加载中：骨架屏，避免白屏 -->
    <div v-if="loading" class="skeleton">
      <div v-for="n in 3" :key="n" class="sk-card">
        <div class="sk-line w40"></div>
        <div class="sk-line"></div>
        <div class="sk-line w70"></div>
      </div>
    </div>

    <main v-else class="content">
      <!-- 1. 基本信息 -->
      <section class="card">
        <div class="card-head">
          <h2 class="card-title">基本信息</h2>
          <span class="card-note">性别来自实名认证</span>
        </div>

        <div class="field-grid">
          <div class="field">
            <label class="field-label">姓名</label>
            <input v-model="form.name" class="input" type="text" maxlength="20" placeholder="请输入姓名" />
          </div>

          <div class="field">
            <label class="field-label">性别</label>
            <div class="readonly-box">
              <span>{{ genderText }}</span>
              <span class="readonly-hint">不可修改</span>
            </div>
          </div>

          <div class="field full">
            <label class="field-label">手机号</label>
            <input v-model="form.phone" class="input" type="tel" inputmode="numeric" maxlength="11" placeholder="请输入手机号" />
          </div>

          <div class="field full">
            <label class="field-label">学历</label>
            <select v-model="form.education" class="input select">
              <option value="">请选择学历</option>
              <option v-for="opt in educationOptions" :key="opt" :value="opt">{{ opt }}</option>
            </select>
          </div>

          <div class="field full">
            <label class="field-label">技能标签</label>
            <div class="skill-editor">
              <span v-for="(skill, index) in skills" :key="skill + index" class="skill-tag">
                {{ skill }}
                <button class="skill-del" type="button" aria-label="删除技能" @click="removeSkill(index)">×</button>
              </span>
              <input
                v-model="skillInput"
                class="skill-input"
                type="text"
                placeholder="输入技能后按回车添加"
                @keydown="onSkillKeydown"
              />
            </div>
            <p class="field-tip">如：叉车证、保洁、会做饭，可添加多个</p>
          </div>
        </div>
      </section>

      <!-- 2. 求职意向 -->
      <section class="card">
        <div class="card-head">
          <h2 class="card-title">求职意向</h2>
        </div>

        <div class="field">
          <label class="field-label">期望岗位</label>
          <input v-model="form.expected_position" class="input" type="text" maxlength="30" placeholder="如：仓库理货员" />
        </div>

        <div class="field">
          <label class="field-label">期望薪资</label>
          <input v-model="form.expected_salary" class="input" type="text" maxlength="20" placeholder="如：5000-7000 元/月" />
        </div>

        <div class="field">
          <label class="field-label">期望区域</label>
          <input v-model="form.expected_area" class="input" type="text" maxlength="30" placeholder="如：二七区、金水区" />
        </div>
      </section>

      <!-- 3. 工作经历 -->
      <section class="card">
        <div class="card-head">
          <h2 class="card-title">工作经历</h2>
          <span class="card-note">可添加多段</span>
        </div>

        <div v-if="jobs.length === 0" class="empty-state">
          <div class="empty-icon">💼</div>
          <p class="empty-title">还没有工作经历</p>
          <p class="empty-sub">添加一段经历，投递成功率更高</p>
        </div>

        <div v-for="(job, index) in jobs" :key="job.key" class="job-item">
          <div class="job-head">
            <span class="job-index">经历 {{ index + 1 }}</span>
            <button class="btn-del" type="button" @click="removeJob(index)">删除</button>
          </div>

          <div class="field-grid">
            <div class="field">
              <label class="field-label">公司名称</label>
              <input v-model="job.company" class="input" type="text" maxlength="40" placeholder="如：XX 物流" />
            </div>
            <div class="field">
              <label class="field-label">职位</label>
              <input v-model="job.position" class="input" type="text" maxlength="30" placeholder="如：理货员" />
            </div>
            <div class="field full">
              <label class="field-label">时间段</label>
              <input v-model="job.period" class="input" type="text" maxlength="30" placeholder="如：2022.03 - 2024.06" />
            </div>
            <div class="field full">
              <label class="field-label">工作内容</label>
              <textarea
                v-model="job.desc"
                class="input textarea"
                rows="3"
                maxlength="500"
                placeholder="简单描述做过什么，如：负责货物分拣、上架，日均处理 500 件"
              ></textarea>
            </div>
          </div>
        </div>

        <button class="btn-add" type="button" @click="addJob">＋ 添加工作经历</button>
      </section>
    </main>

    <!-- 底部固定保存按钮（高于全局底部导航） -->
    <div v-if="!loading" class="save-bar">
      <button class="btn-save" type="button" :disabled="saving" @click="saveResume">
        {{ saving ? '保存中…' : '保存简历' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()

const loading = ref(true)
const saving = ref(false)
const skillInput = ref('')
const profileGender = ref('')
const extraBasic = ref({})
const skills = ref([])
const jobs = ref([])

const form = reactive({
  name: '',
  phone: '',
  email: '',
  education: '',
  expected_position: '',
  expected_salary: '',
  expected_area: ''
})

const EDUCATION_OPTIONS = ['初中及以下', '高中/中专', '大专', '本科', '硕士及以上']
const BASIC_FIELDS = [
  'name', 'phone', 'email', 'skills', 'education',
  'expected_position', 'expected_salary', 'expected_area'
]

let jobSeq = 0

const toText = (value) => (value === null || value === undefined ? '' : String(value))

const educationOptions = computed(() => {
  const options = [...EDUCATION_OPTIONS]
  if (form.education && !options.includes(form.education)) {
    options.unshift(form.education)
  }
  return options
})

const genderText = computed(() => {
  const gender = profileGender.value
  return gender && gender !== '未知' ? gender : '未填写'
})

const makeJob = (data = {}) => ({
  key: ++jobSeq,
  company: toText(data.company),
  position: toText(data.position),
  period: toText(data.period),
  desc: toText(data.desc)
})

const hydrateResume = (data) => {
  const resume = data && typeof data === 'object' ? data : {}
  const basic = resume.basic && typeof resume.basic === 'object' ? resume.basic : {}

  form.name = toText(basic.name)
  form.phone = toText(basic.phone)
  form.email = toText(basic.email)
  form.education = toText(basic.education)
  form.expected_position = toText(basic.expected_position)
  form.expected_salary = toText(basic.expected_salary)
  form.expected_area = toText(basic.expected_area)

  const rawSkills = basic.skills
  if (Array.isArray(rawSkills)) {
    skills.value = rawSkills.map(toText).map(s => s.trim()).filter(Boolean)
  } else {
    skills.value = toText(rawSkills)
      .split(/[,，、]/)
      .map(s => s.trim())
      .filter(Boolean)
  }

  const extra = {}
  Object.keys(basic).forEach((key) => {
    if (!BASIC_FIELDS.includes(key)) extra[key] = basic[key]
  })
  extraBasic.value = extra

  jobs.value = Array.isArray(resume.jobs) ? resume.jobs.map(makeJob) : []
}

onMounted(async () => {
  const [resumeResult, profileResult] = await Promise.allSettled([
    api.get('/user/resume'),
    api.get('/user/profile')
  ])

  if (resumeResult.status === 'fulfilled') {
    hydrateResume(resumeResult.value?.data)
  } else {
    window.$toast('简历加载失败，请稍后重试')
  }

  if (profileResult.status === 'fulfilled') {
    const profile = profileResult.value?.data || {}
    profileGender.value = toText(profile.gender)
    if (!form.name) form.name = toText(profile.real_name)
  }

  // 手机号兜底：本地登录信息
  if (!form.phone) {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      form.phone = toText(user.phone)
    } catch (err) {
      // 本地数据异常时忽略即可
    }
  }

  loading.value = false
})

const addSkill = () => {
  const raw = skillInput.value.trim()
  if (!raw) return

  const parts = raw.split(/[,，、]/).map(s => s.trim()).filter(Boolean)
  let added = 0
  parts.forEach((part) => {
    if (!skills.value.includes(part)) {
      skills.value.push(part)
      added += 1
    }
  })

  skillInput.value = ''
  if (added === 0) window.$toast('该技能已添加')
}

const onSkillKeydown = (event) => {
  if (event.key !== 'Enter') return
  if (event.isComposing || event.keyCode === 229) return
  event.preventDefault()
  addSkill()
}

const removeSkill = (index) => {
  skills.value.splice(index, 1)
}

const addJob = () => {
  jobs.value.push(makeJob())
}

const removeJob = (index) => {
  if (window.confirm('确定删除这段工作经历吗？')) {
    jobs.value.splice(index, 1)
  }
}

const saveResume = async () => {
  if (saving.value) return

  const name = form.name.trim()
  const phone = form.phone.trim()
  if (!name) return window.$toast('请填写姓名')
  if (!phone) return window.$toast('请填写手机号')

  const basicPayload = {
    ...extraBasic.value,
    name,
    phone,
    email: form.email.trim(),
    skills: skills.value.join(','),
    education: form.education || '',
    expected_position: form.expected_position.trim(),
    expected_salary: form.expected_salary.trim(),
    expected_area: form.expected_area.trim()
  }

  const jobsPayload = jobs.value.map(job => ({
    company: toText(job.company),
    position: toText(job.position),
    period: toText(job.period),
    desc: toText(job.desc)
  }))

  saving.value = true
  try {
    await api.put('/user/resume', {
      basic: basicPayload,
      jobs: jobsPayload
    })
    window.$toast('简历保存成功')
    setTimeout(() => { router.back() }, 800)
  } catch (err) {
    saving.value = false
    window.$toast(err?.response?.data?.detail || '保存失败，请稍后重试')
  }
}
</script>

<style scoped>
.resume-page {
  min-height: 100vh;
  box-sizing: border-box;
  background: #f5f7fa;
  padding-bottom: 90px;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #111;
}

.resume-page * {
  box-sizing: border-box;
}

/* 顶部标题区 */
.page-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 20px 4px;
}

.back-btn {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  padding: 0;
  border: none;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.head-text h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  line-height: 1.3;
  color: #111;
}

.head-text p {
  margin: 4px 0 0;
  font-size: 13px;
  line-height: 1.4;
  color: #7b8797;
}

.content {
  padding: 16px 16px 60px;
}

/* 卡片 */
.card {
  background: #fff;
  border-radius: 16px;
  padding: 18px 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
  margin-bottom: 12px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 16px;
}

.card-title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  line-height: 1.3;
  color: #111;
}

.card-note {
  flex-shrink: 0;
  font-size: 13px;
  color: #7b8797;
}

/* 表单 */
.field-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px 12px;
}

.field {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.field.full {
  grid-column: 1 / -1;
}

.card .field + .field {
  margin-top: 14px;
}

.field-grid .field + .field {
  margin-top: 0;
}

.field-label {
  margin-bottom: 7px;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.4;
  color: #7b8797;
}

.input {
  width: 100%;
  height: 52px;
  padding: 0 14px;
  border: 1px solid #eee;
  border-radius: 12px;
  background-color: #f5f7fa;
  font-family: inherit;
  font-size: 16px;
  color: #111;
  outline: none;
  transition: border-color 0.2s, background-color 0.2s;
}

.input::placeholder {
  color: #a9b2be;
}

.input:focus {
  border-color: #ff6b00;
  background-color: #fff;
}

.textarea {
  height: auto;
  min-height: 96px;
  padding: 12px 14px;
  line-height: 1.6;
  resize: vertical;
}

.select {
  appearance: none;
  -webkit-appearance: none;
  padding-right: 36px;
  background-image:
    linear-gradient(45deg, transparent 50%, #7b8797 50%),
    linear-gradient(135deg, #7b8797 50%, transparent 50%);
  background-position:
    calc(100% - 19px) 23px,
    calc(100% - 14px) 23px;
  background-repeat: no-repeat;
  background-size: 5px 5px, 5px 5px;
}

/* 只读展示 */
.readonly-box {
  height: 52px;
  padding: 0 14px;
  border: 1px solid #eee;
  border-radius: 12px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  font-size: 16px;
  color: #111;
}

.readonly-hint {
  flex-shrink: 0;
  font-size: 11px;
  color: #a9b2be;
}

/* 技能标签编辑器 */
.skill-editor {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  min-height: 52px;
  padding: 7px 10px;
  border: 1px solid #eee;
  border-radius: 12px;
  background: #f5f7fa;
  transition: border-color 0.2s, background-color 0.2s;
}

.skill-editor:focus-within {
  border-color: #ff6b00;
  background: #fff;
}

.skill-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 6px 5px 10px;
  border-radius: 6px;
  background: #fff1e6;
  color: #ff6b00;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.2;
}

.skill-del {
  padding: 0 2px;
  border: none;
  background: transparent;
  color: #ff6b00;
  font-size: 15px;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
}

.skill-input {
  flex: 1 1 140px;
  min-width: 120px;
  height: 34px;
  padding: 0 2px;
  border: none;
  outline: none;
  background: transparent;
  font-family: inherit;
  font-size: 16px;
  color: #111;
}

.skill-input::placeholder {
  color: #a9b2be;
}

.field-tip {
  margin: 7px 2px 0;
  font-size: 13px;
  line-height: 1.4;
  color: #a9b2be;
}

/* 工作经历 */
.job-item {
  padding: 14px;
  margin-bottom: 12px;
  border: 1px solid #f0f2f5;
  border-radius: 14px;
  background: #fff;
}

.job-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.job-index {
  padding: 3px 10px;
  border-radius: 6px;
  background: #fff1e6;
  color: #ff6b00;
  font-size: 13px;
  font-weight: 700;
}

.btn-del {
  padding: 5px 12px;
  border: none;
  border-radius: 8px;
  background: #fef2f2;
  color: #ef4444;
  font-family: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.job-item .field-grid {
  gap: 12px;
}

.empty-state {
  padding: 18px 8px 20px;
  text-align: center;
}

.empty-icon {
  margin-bottom: 8px;
  font-size: 32px;
  line-height: 1;
}

.empty-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #111;
}

.empty-sub {
  margin: 6px 0 0;
  font-size: 13px;
  color: #7b8797;
}

.btn-add {
  width: 100%;
  height: 50px;
  margin-top: 2px;
  border: 1px dashed #ffb27a;
  border-radius: 12px;
  background: #fff1e6;
  color: #ff6b00;
  font-family: inherit;
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
}

.btn-add:active {
  opacity: 0.85;
}

/* 底部固定保存按钮 */
.save-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 64px;
  z-index: 90;
  padding: 10px 16px 12px;
  background: linear-gradient(to top, #f5f7fa 55%, rgba(245, 247, 250, 0));
}

.btn-save {
  display: block;
  width: 100%;
  height: 52px;
  border: none;
  border-radius: 12px;
  background: #ff6b00;
  color: #fff;
  font-family: inherit;
  font-size: 17px;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(255, 107, 0, 0.28);
}

.btn-save:disabled {
  background: #ffb27a;
  box-shadow: none;
  cursor: not-allowed;
}

.btn-save:active:not(:disabled) {
  transform: translateY(1px);
}

/* 骨架屏 */
.skeleton {
  padding: 16px;
}

.sk-card {
  padding: 20px;
  margin-bottom: 12px;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}

.sk-line {
  height: 16px;
  margin-bottom: 12px;
  border-radius: 8px;
  background: #eef1f5;
  animation: sk-pulse 1.2s ease-in-out infinite;
}

.sk-line:last-child {
  margin-bottom: 0;
}

.sk-line.w40 {
  width: 40%;
  height: 20px;
}

.sk-line.w70 {
  width: 70%;
}

@keyframes sk-pulse {
  0%, 100% {
    opacity: 0.55;
  }
  50% {
    opacity: 1;
  }
}
</style>
