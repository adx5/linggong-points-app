<!-- frontend/src/views/worker/WorkerResume.vue (C端简历维护：按ATS机读规范与STAR法则设计) -->
<template>
  <div class="resume-page">
    <div class="sticky-header">
      <div class="header-left">
        <div class="btn-back" @click="$router.back()">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#1f2937" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
        </div>
        <h2>简历维护</h2>
      </div>
      <span class="btn-preview" @click="previewResume">预览</span>
    </div>

    <div class="content">
      <!-- 顶部提示 -->
      <div class="tips-box">
        💡 提示：简历请按“STAR法则”填写。多写数据和结果（如：协调30人、提升20%效率），少写空话套话。请使用标准格式日期（如：2022.07-2024.06）。
      </div>

      <div class="form-card">
        <!-- 1. 个人信息 -->
        <h3 class="section-title">1. 基本信息</h3>
        <div class="row-group">
          <input v-model="form.name" placeholder="姓名" />
          <input v-model="form.phone" placeholder="手机号" type="tel" maxlength="11" />
        </div>
        <input v-model="form.email" placeholder="邮箱 (建议使用专业邮箱，避免QQ数字串)" type="email" style="margin-top: 10px;"/>

        <!-- 2. 求职意向 -->
        <h3 class="section-title">2. 求职意向</h3>
        <div class="row-group">
          <input v-model="form.target_job" placeholder="期望岗位 (如：普工/新媒体运营)" style="flex: 1.5;" />
          <input v-model="form.target_city" placeholder="期望城市/区域" style="flex: 1;" />
        </div>

        <!-- 3. 核心技能 -->
        <h3 class="section-title">3. 核心技能</h3>
        <textarea v-model="form.skills" placeholder="按相关度排序，用逗号或竖线分隔。&#10;如：Excel(精通数据透视表) | 叉车证(持证) | 驾驶(5年经验)" rows="2"></textarea>

        <!-- 4. 工作与项目经历 -->
        <h3 class="section-title">4. 工作 / 项目经历 (重点)</h3>
        <textarea v-model="form.work_experience" placeholder="【工作经历】&#10;公司名称 | 岗位 | 起止时间&#10;按STAR法则填写：&#10;· 负责XXX工作，通过XXX方法，达成XXX结果（量化）。&#10;&#10;【若无工作经验，可写项目/校园经历】&#10;· 在校期间策划XXX活动，协调30人参与，到场率90%。" rows="6"></textarea>

        <!-- 5. 教育背景 -->
        <h3 class="section-title">5. 教育背景</h3>
        <textarea v-model="form.education" placeholder="学校名称 | 专业 | 学历 | 起止时间&#10;如：郑州大学 | 机械工程 | 大专 | 2020.09-2023.06" rows="2"></textarea>

        <!-- 6. 自我评价 -->
        <h3 class="section-title">6. 自我评价 (50-80字)</h3>
        <textarea v-model="form.self_evaluation" placeholder="拒绝套话。结合岗位要求，提炼2-3点核心优势。&#10;例如：具备3年制造业产线调试经验；曾主导产线改造项目，将良品率提升15%；执行力强，能适应倒班作业。" rows="3"></textarea>
      </div>

      <div class="bottom-bar">
        <button class="btn-save" @click="saveResume" :disabled="saving">
          {{ saving ? '保存中...' : '保存简历' }}
        </button>
      </div>
    </div>

    <!-- 预览弹窗 -->
    <div v-if="showPreview" class="modal-overlay" @click.self="showPreview = false">
      <div class="modal-content">
        <h3>简历预览</h3>
        <div class="preview-text">
          <p><strong>姓名：</strong>{{ form.name }} | {{ form.phone }} | {{ form.email }}</p>
          <p><strong>意向：</strong>{{ form.target_job }} ({{ form.target_city }})</p>
          <p><strong>技能：</strong>{{ form.skills }}</p>
          <p><strong>经历：</strong><br>{{ form.work_experience }}</p>
          <p><strong>教育：</strong><br>{{ form.education }}</p>
          <p><strong>评价：</strong>{{ form.self_evaluation }}</p>
        </div>
        <div class="modal-btns">
          <button class="btn-close" @click="showPreview = false">关闭</button>
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
const showPreview = ref(false)

const form = reactive({
  name: '', phone: '', email: '',
  target_job: '', target_city: '',
  skills: '', work_experience: '', project_experience: '', education: '', self_evaluation: ''
})

onMounted(async () => {
  try {
    const res = await api.get('/user/resume')
    if (res.data) {
      Object.assign(form, res.data)
    }
    // 顺手把手机号填上
    const userStr = localStorage.getItem('user')
    if (userStr && !form.phone) {
      const u = JSON.parse(userStr)
      if(u.phone) form.phone = u.phone
    }
  } catch (err) {
    console.error('获取简历失败', err)
  }
})

const previewResume = () => {
  if (!form.name) return window.$toast('请至少填写姓名')
  showPreview.value = true
}

const saveResume = async () => {
  if (!form.name || !form.phone || !form.target_job) {
    return window.$toast('请填写必填项：姓名、手机号、期望岗位')
  }

  saving.value = true
  try {
    await api.put('/user/resume', form)
    window.$toast('简历保存成功')
    setTimeout(() => { router.back() }, 1000)
  } catch (err) {
    window.$toast('保存失败，请检查网络')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.resume-page { min-height: 100vh; background: #f5f6f8; padding-bottom: 80px; }
.sticky-header { position: sticky; top: 0; z-index: 99; background: #fff; padding: 16px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
.header-left { display: flex; align-items: center; gap: 8px; }
.btn-back { cursor: pointer; display: flex; align-items: center; margin-left: -8px; }
.sticky-header h2 { font-size: 18px; color: #1f2937; font-weight: bold; }
.btn-preview { font-size: 14px; color: #2563eb; cursor: pointer; font-weight: bold; }

.content { padding: 16px; }
.tips-box { background: #eff6ff; color: #2563eb; font-size: 13px; padding: 12px; border-radius: 8px; margin-bottom: 16px; border: 1px solid #bfdbfe; line-height: 1.5; }

.form-card { background: #fff; border-radius: 12px; padding: 16px; }
.section-title { font-size: 15px; font-weight: bold; color: #1f2937; margin: 20px 0 12px; padding-left: 8px; border-left: 3px solid #2563eb; }
.section-title:first-child { margin-top: 0; }

.row-group { display: flex; gap: 10px; }
.row-group input { flex: 1; }

input, textarea { width: 100%; padding: 12px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; outline: none; background: #f9fafb; font-family: inherit; }
input:focus, textarea:focus { border-color: #2563eb; background: #fff; }
textarea { resize: vertical; margin-top: 10px; }

.bottom-bar { position: fixed; bottom: 0; left: 0; right: 0; padding: 12px 16px; background: #fff; box-shadow: 0 -2px 10px rgba(0,0,0,0.05); padding-bottom: env(safe-area-inset-bottom); z-index: 100; }
.btn-save { width: 100%; background: #10b981; color: #fff; padding: 14px; border-radius: 8px; font-size: 16px; font-weight: bold; border: none; cursor: pointer; }
.btn-save:disabled { opacity: 0.7; }

/* 弹窗 */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 999; display: flex; justify-content: center; align-items: center; }
.modal-content { background: #fff; width: 90%; border-radius: 12px; padding: 20px; max-height: 80vh; overflow-y: auto; }
.modal-content h3 { text-align: center; margin-bottom: 16px; font-size: 18px; font-weight: bold; }
.preview-text { background: #f9fafb; padding: 16px; border-radius: 8px; font-size: 13px; color: #333; line-height: 1.6; }
.preview-text p { margin-bottom: 12px; }
.preview-text strong { color: #1f2937; }
.modal-btns { margin-top: 16px; }
.btn-close { width: 100%; background: #f3f4f6; color: #666; padding: 12px; border-radius: 6px; font-weight: bold; border: none; cursor: pointer; }
</style>