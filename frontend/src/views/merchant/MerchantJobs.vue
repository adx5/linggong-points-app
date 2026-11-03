<!-- (B端发布岗位：带历史岗位一键复制功能) -->
<template>
  <div class="jobs-page">
    <div class="sticky-header">
      <div class="header-left">
        <div class="btn-back" @click="$router.back()">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#1f2937" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
        </div>
        <h2>发布新岗位</h2>
      </div>
      <!-- 🚨 新增：一键复制入口 -->
      <button class="btn-copy-history" @click="openCopyModal">📋 复制历史</button>
    </div>

    <div class="content">
      <div class="form-box">
        <!-- 1. 顶部用工类型 (防呆设计) -->
        <div class="type-selector">
          <div class="type-btn" :class="{ active: form.job_type === 'long_term' }" @click="changeJobType('long_term')">
            长期稳定用工
          </div>
          <div class="type-btn" :class="{ active: form.job_type === 'short_term' }" @click="changeJobType('short_term')">
            短期灵活用工
          </div>
        </div>

        <!-- 基础信息：标题与分类同行 -->
        <div class="row-group">
          <input v-model="form.title" placeholder="招聘岗位 (如: 普工、发传单、叉车工)" style="flex: 1;" />
          <select v-model="form.filter_tag" style="flex: 0 0 110px;">
            <option value="">岗位分类</option>
            <option v-for="tag in currentFilterTags" :key="tag" :value="tag">{{ tag }}</option>
          </select>
        </div>

        <!-- 2. 薪资模块拆分 -->
        <div class="section-title">薪资结算</div>
        <div class="row-group">
          <select v-model="form.salary_type" style="flex: 0 0 90px;">
            <option value="月薪">月薪</option>
            <option value="日薪">日薪</option>
            <option value="时薪">时薪</option>
            <option value="计件">计件</option>
          </select>

          <div class="input-group">
            <input type="number" v-model="form.salary_min" placeholder="最低" />
            <span class="separator">至</span>
            <input type="number" v-model="form.salary_max" placeholder="最高" />
          </div>

          <div class="input-group" style="flex: 0 0 110px;" v-if="form.job_type === 'long_term' || form.salary_type === '月薪'">
            <input type="number" v-model="form.pay_date" placeholder="几号发" />
          </div>

          <select v-model="form.settle_method" style="flex: 0 0 110px;" v-if="form.job_type === 'short_term' && form.salary_type !== '月薪'">
            <option value="下班后结">下班后结</option>
            <option value="次日中午结">次日中午结</option>
            <option value="周结">周结</option>
          </select>
        </div>

        <!-- 3. 工作地点 -->
        <div class="section-title">工作地点</div>
        <div class="row-group" style="margin-bottom: 8px;">
          <select v-model="form.province" @change="handleProvinceChange">
            <option value="">省份</option>
            <option v-for="p in provinceData" :key="p.name" :value="p.name">{{ p.name }}</option>
          </select>
          <select v-model="form.city" @change="handleCityChange" :disabled="!form.province">
            <option value="">城市</option>
            <option v-for="c in currentCities" :key="c.name" :value="c.name">{{ c.name }}</option>
          </select>
          <select v-model="form.district" :disabled="!form.city">
            <option value="">区/县</option>
            <option v-for="d in currentDistricts" :key="d" :value="d">{{ d }}</option>
          </select>
        </div>
        <div class="row-group">
          <input v-model="form.location_text" placeholder="详细地址 (如: XX工业园)" style="flex: 1;" />
          <button class="btn-map" @click="chooseLocationFromMap">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
            地图选点
          </button>
        </div>

        <!-- 4. 福利保障标签区 -->
        <div class="compact-tag-area">
          <div class="tag-list">
            <span class="group-label">福利保障（多选）：</span>
            <div v-for="tag in currentMixedTags" :key="tag" class="tag-btn" :class="{ active: form.tags.includes(tag) }" @click="toggleArrayItem(form.tags, tag)">
              {{ tag }}
            </div>
          </div>
        </div>

        <!-- 5. 人员要求 -->
        <div class="section-title">人员要求</div>
        <div class="row-group">
          <select v-model="form.age_range">
            <option value="16-35岁">16-35岁</option>
            <option value="18-45岁">18-45岁</option>
            <option value="45-60岁">45-60岁</option>
            <option value="年龄不限">年龄不限</option>
          </select>
          <select v-model="form.gender">
            <option value="男女不限">男女不限</option>
            <option value="男士优先">男士优先</option>
            <option value="女士优先">女士优先</option>
          </select>
        </div>
        <input v-model="form.special_req" placeholder="特殊要求 (如：需无犯罪记录 / 50岁以上需体检)" style="margin-top: 10px;" />

        <!-- 岗位介绍与快捷短语 -->
        <div class="section-title">岗位介绍</div>
        <div class="quick-phrases">
          <span v-for="phrase in quickPhrases" :key="phrase" @click="insertPhrase(phrase)" class="phrase-chip">{{ phrase }}</span>
        </div>
        <textarea v-model="form.description" placeholder="岗位介绍..." rows="3" class="textarea-box"></textarea>

        <!-- 6. 费用说明 -->
        <div class="section-title" style="color: #ef4444;">费用说明 (必选，可多选)</div>
        <div class="cost-row">
          <label class="checkbox-item">
            <input type="checkbox" v-model="form.cost_free" @change="handleCostFreeChange" /> 纯免费
          </label>
        </div>
        <div class="cost-row">
          <label class="checkbox-item">
            <input type="checkbox" v-model="form.cost_medical" @change="handleCostOtherChange" /> 体检费自理
          </label>
          <input v-if="form.cost_medical" v-model="form.cost_medical_note" placeholder="如: 50元，满月报销" class="cost-input" />
        </div>
        <div class="cost-row">
          <label class="checkbox-item">
            <input type="checkbox" v-model="form.cost_uniform" @change="handleCostOtherChange" /> 需工服/押金
          </label>
          <input v-if="form.cost_uniform" v-model="form.cost_uniform_note" placeholder="如: 工服押金100，离职退还" class="cost-input" />
        </div>

        <div class="btn-group">
          <button class="btn-cancel" @click="$router.back()">取消</button>
          <button class="btn-submit" @click="previewJob">预览并发布</button>
        </div>
      </div>
    </div>

    <!-- 🚨 一键复制历史岗位弹窗 -->
    <div v-if="showCopyModal" class="modal-overlay" @click.self="showCopyModal = false">
      <div class="modal-content copy-modal">
        <h3>一键复制历史岗位</h3>
        <div class="history-list">
          <div class="history-item" v-for="job in historyJobs" :key="job.id" @click="copyJob(job)">
            <div class="h-title">{{ job.title }}</div>
            <div class="h-salary">{{ job.salary }}</div>
          </div>
          <div v-if="historyJobs.length === 0" class="empty">暂无历史岗位可复制</div>
        </div>
        <button class="btn-close" @click="showCopyModal = false">关闭</button>
      </div>
    </div>

    <!-- 发布预览弹窗 -->
    <div v-if="showPreview" class="modal-overlay">
      <div class="modal-content">
        <h3>确认发布信息</h3>
        <div class="preview-card">
          <div class="row"><h4>{{ form.title }}</h4><span class="price">{{ previewSalary }}</span></div>
          <div class="tags">
            <span>{{ form.filter_tag }}</span>
            <span>{{ form.job_type === 'long_term' ? '长期' : '短期' }}</span>
            <span v-for="tag in form.tags" :key="tag">{{ tag }}</span>
          </div>
          <p class="loc">📍 {{ previewLocation }}</p>
          <p class="req">人员要求：{{ form.age_range }} | {{ form.gender }}</p>
          <div class="cost" style="color: #ef4444; font-weight: bold;">费用：{{ previewCost }}</div>
        </div>
        <div class="modal-btns">
          <button class="btn-cancel" @click="showPreview = false">返回修改</button>
          <button class="btn-submit" @click="submit">确认发布</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()

const form = reactive({
  title: '', salary_type: '月薪', salary_min: '', salary_max: '', pay_date: '', settle_method: '下班后结',
  province: '', city: '', district: '', location_text: '', job_type: 'long_term', filter_tag: '', tags: [],
  age_range: '18-45岁', gender: '男女不限', special_req: '', description: '',
  cost_free: false, cost_medical: false, cost_medical_note: '', cost_uniform: false, cost_uniform_note: ''
})

const provinceData = [
  { name: '河南省', cities: [{ name: '郑州市', districts: ['中原区', '二七区', '金水区', '惠济区', '管城区', '郑东新区', '高新区', '经开区', '航空港区'] }] },
  { name: '广东省', cities: [{ name: '广州市', districts: ['天河区', '越秀区', '海珠区', '番禺区', '白云区'] }] }
]
const currentCities = computed(() => {
  const p = provinceData.find(item => item.name === form.province)
  return p ? p.cities : []
})
const currentDistricts = computed(() => {
  const c = currentCities.value.find(item => item.name === form.city)
  return c ? c.districts : []
})
const handleProvinceChange = () => { form.city = ''; form.district = '' }
const handleCityChange = () => { form.district = '' }
const chooseLocationFromMap = () => {
  window.$toast('正在拉起地图...')
  setTimeout(() => { form.location_text = '郑州市高新区科学大道100号 (模拟地图坐标)' }, 800)
}

const quickPhrases = ['不穿无尘服', '站班/坐班', '包吃三菜一汤', '有地牛/推车辅助', '无需经验']
const longTermFilterTags = ['正式工岗', '厂区直招', '技术工种', '长白班岗', '大龄兜底', '包吃包住', '就近通勤', '稳定月结']
const shortTermFilterTags = ['日结周结', '外卖快递', '活动促销', '分拣搬运', '餐饮兼职', '展会临勤', '学生假期', '宝妈兼职']
const longTermMixedTags = ['包吃', '包住', '包吃包住', '有班车', '厂车接送', '长白班', '两班倒', '五险一金', '周末双休', '月休四天', '带薪培训', '年终奖', '节日福利', '年底双薪', '定期体检', '高温补贴', '全勤奖', '夫妻房', '水电全免', '可预支工资']
const shortTermMixedTags = ['日结', '下班结', '次日结', '周结', '包接送', '管饭', '包吃住', '提供住宿', '轻松不累', '当天入职', '完工结算', '工作餐', '长白班', '坐班', '不穿无尘服', '无需体检', '可带手机', '有休息室']

const currentFilterTags = computed(() => form.job_type === 'long_term' ? longTermFilterTags : shortTermFilterTags)
const currentMixedTags = computed(() => form.job_type === 'long_term' ? longTermMixedTags : shortTermMixedTags)

const changeJobType = (type) => {
  form.job_type = type
  form.filter_tag = ''
  form.tags = []
  if (type === 'short_term') { form.salary_type = '日薪' } else { form.salary_type = '月薪' }
}

const toggleArrayItem = (arr, item) => {
  const index = arr.indexOf(item)
  if (index > -1) arr.splice(index, 1)
  else arr.push(item)
}

const insertPhrase = (phrase) => {
  form.description = form.description ? `${form.description} ${phrase}。` : `${phrase}。`
}
const handleCostFreeChange = () => {
  if (form.cost_free) { form.cost_medical = false; form.cost_medical_note = ''; form.cost_uniform = false; form.cost_uniform_note = '' }
}
const handleCostOtherChange = () => {
  if (form.cost_medical || form.cost_uniform) { form.cost_free = false }
}

const previewSalary = computed(() => {
  if (!form.salary_min && !form.salary_max) return '面议'
  const range = form.salary_min ? (form.salary_max ? `${form.salary_min}-${form.salary_max}` : `${form.salary_min}以上`) : form.salary_max
  const suffix = form.salary_type === '月薪' ? (form.pay_date ? ` ${form.pay_date}号发` : '') : ` ${form.settle_method}`
  return `${form.salary_type} ${range}元${suffix}`
})
const previewLocation = computed(() => {
  const area = form.province ? `${form.province} ${form.city} ${form.district}` : ''
  return `${area} ${form.location_text}`.trim()
})
const previewCost = computed(() => {
  const costs = []
  if (form.cost_free) costs.push('纯免费')
  if (form.cost_medical) costs.push(`体检费自理(${form.cost_medical_note || '待沟通'})`)
  if (form.cost_uniform) costs.push(`需工服/押金(${form.cost_uniform_note || '待沟通'})`)
  return costs.join('，') || '未选择'
})

// 🚨 历史岗位弹窗逻辑
const showCopyModal = ref(false)
const historyJobs = ref([])

const openCopyModal = async () => {
  showCopyModal.value = true
  try {
    const res = await api.get('/jobs/my-list')
    historyJobs.value = res.data || []
  } catch (err) {
    window.$toast('获取历史岗位失败')
  }
}

const copyJob = (job) => {
  form.title = job.title
  form.job_type = job.job_type
  form.filter_tag = job.filter_tag
  form.tags = job.tags ? job.tags.split(',').filter(t => t) : []

  const numMatch = job.salary.match(/\d+/g)
  if (numMatch) {
    form.salary_min = numMatch[0] || ''
    form.salary_max = numMatch[1] || ''
  }

  form.location_text = job.location
  form.description = job.description || ''
  form.requirement = job.requirement || ''

  if (!form.title.includes('(复制)')) {
    form.title += ' (复制)'
  }

  showCopyModal.value = false
  window.$toast('已成功复制岗位信息')
}

// 提交逻辑
const showPreview = ref(false)
const previewJob = () => {
  if (!form.title) return window.$toast('请填写岗位名称')
  if (!form.filter_tag) return window.$toast('请选择岗位分类')
  if (!form.location_text) return window.$toast('请填写详细地址或使用地图选点')
  if (!form.cost_free && !form.cost_medical && !form.cost_uniform) return window.$toast('请选择费用说明')
  showPreview.value = true
}

const submit = async () => {
  showPreview.value = false
  window.$toast('正在发布...')
  const payload = {
    title: form.title, salary: previewSalary.value, location: previewLocation.value,
    job_type: form.job_type, filter_tag: form.filter_tag, tags: form.tags.join(','),
    description: `${form.description}\n【费用说明】${previewCost.value}`,
    requirement: `年龄：${form.age_range}，性别：${form.gender}。特殊要求：${form.special_req}`
  }
  try {
    const res = await api.post('/jobs/create', payload)
    if (res.status === 'draft') {
      setTimeout(() => {
        const wantToVerify = window.confirm('岗位已保存至草稿箱！\n完成企业备案后，该岗位将自动对外公开展示。\n是否现在去完成备案？');
        if (wantToVerify) router.push('/merchant/verify')
        else router.push('/merchant/job-list')
      }, 500)
    } else {
      window.$toast('发布成功，已进入展示列表')
      setTimeout(() => router.push('/merchant/job-list'), 1000)
    }
  } catch (e) { window.$toast('发布失败，请检查网络') }
}

onMounted(() => {})
</script>

<style scoped>
/* 保持原有样式不变 */
.jobs-page { min-height: 100vh; background: #f0f2f5; }
.sticky-header { position: sticky; top: 0; z-index: 99; background: #fff; padding: 16px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
.header-left { display: flex; align-items: center; gap: 8px; }
.btn-back { cursor: pointer; display: flex; align-items: center; margin-left: -8px; }
.sticky-header h2 { font-size: 18px; color: #1f2937; }
.btn-copy-history { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: bold; cursor: pointer; }

.content { padding: 16px; }
.form-box { background: #fff; padding: 20px; border-radius: 12px; display: flex; flex-direction: column; gap: 16px; }

.type-selector { display: flex; gap: 10px; margin-bottom: 10px; }
.type-btn { flex: 1; text-align: center; padding: 12px; border-radius: 8px; background: #f3f4f6; color: #666; font-weight: bold; transition: all 0.2s; cursor: pointer; }
.type-btn.active { background: #2563eb; color: #fff; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); }

input, select, .textarea-box { width: 100%; padding: 12px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; background: #fff; color: #333; outline: none; font-family: inherit; }
input:focus, select:focus, .textarea-box:focus { border-color: #2563eb; }
input:disabled, select:disabled { background: #f9fafb; color: #9ca3af; cursor: not-allowed; }
.textarea-box { resize: vertical; }

.section-title { font-size: 14px; font-weight: bold; color: #1f2937; margin-top: 10px; margin-bottom: -6px; }
.row-group { display: flex; gap: 8px; align-items: center; }
.input-group { display: flex; align-items: center; background: #fff; border: 1px solid #e5e7eb; border-radius: 6px; padding: 0 8px; flex: 1; }
.input-group input { border: none; padding: 12px 0; text-align: center; }
.input-group:focus-within { border-color: #2563eb; }
.separator { color: #999; font-size: 12px; padding: 0 4px; }

.btn-map { display: flex; align-items: center; gap: 4px; white-space: nowrap; padding: 0 12px; height: 42px; background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; border-radius: 6px; font-size: 14px; font-weight: bold; cursor: pointer; }

.compact-tag-area { display: flex; background: #fafafa; padding: 12px; border-radius: 8px; border: 1px solid #f3f4f6; margin-top: -6px; }
.tag-list { display: flex; flex-wrap: wrap; gap: 8px 6px; width: 100%; align-items: flex-start; }
.group-label { font-size: 14px; color: #1f2937; font-weight: bold; white-space: nowrap; margin-right: 4px; height: 26px; line-height: 26px; }
.tag-btn { padding: 2px 8px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 4px; font-size: 12px; color: #2563eb; cursor: pointer; transition: all 0.2s; height: 26px; box-sizing: border-box; line-height: 20px; }
.tag-btn.active { background: #2563eb; color: #fff; font-weight: bold; border-color: #2563eb; }

.quick-phrases { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.phrase-chip { padding: 2px 8px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 4px; font-size: 12px; color: #2563eb; cursor: pointer; height: 26px; line-height: 20px; box-sizing: border-box; }
.phrase-chip:active { background: #d1d5db; }

.cost-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 4px; }
.checkbox-item { display: flex; align-items: center; gap: 6px; font-size: 14px; color: #374151; cursor: pointer; white-space: nowrap; }
.checkbox-item input[type="checkbox"] { width: 16px; height: 16px; margin: 0; cursor: pointer; }
.cost-input { flex: 1; min-width: 150px; padding: 6px 10px; border: 1px dashed #ef4444; background: #fef2f2; color: #ef4444; border-radius: 4px; font-size: 13px; outline: none; }
.cost-input::placeholder { color: #fca5a5; }

.btn-group { display: flex; gap: 12px; margin-top: 20px; }
.btn-group button { flex: 1; padding: 14px; border-radius: 6px; font-weight: bold; font-size: 16px; }
.btn-cancel { background: #f3f4f6; color: #666; border: none; cursor: pointer; }
.btn-submit { background: #10b981; color: #fff; border: none; cursor: pointer; }

/* 弹窗通用 */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 999; display: flex; justify-content: center; align-items: center; }
.modal-content { background: #fff; width: 90%; border-radius: 12px; padding: 20px; }
.modal-content h3 { text-align: center; margin-bottom: 16px; font-size: 18px; }
.preview-card { background: #f9fafb; padding: 16px; border-radius: 8px; border: 1px dashed #d1d5db; margin-bottom: 20px; }
.preview-card .row { display: flex; justify-content: space-between; margin-bottom: 8px; }
.preview-card .price { color: #ef4444; font-weight: bold; }
.preview-card .tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
.preview-card .tags span { background: #eff6ff; color: #2563eb; font-size: 12px; padding: 2px 8px; border-radius: 4px; }
.preview-card .loc, .preview-card .req, .preview-card .cost { font-size: 13px; color: #666; margin-bottom: 6px; }
.modal-btns { display: flex; gap: 12px; }

/* 🚨 复制弹窗特有样式 */
.copy-modal { display: flex; flex-direction: column; max-height: 80vh; }
.history-list { flex: 1; overflow-y: auto; margin-bottom: 16px; background: #f9fafb; border-radius: 8px; padding: 8px; }
.history-item { background: #fff; padding: 12px; border-radius: 6px; margin-bottom: 8px; border: 1px solid #e5e7eb; cursor: pointer; transition: all 0.2s; }
.history-item:active { background: #eff6ff; border-color: #2563eb; }
.h-title { font-size: 15px; color: #1f2937; font-weight: bold; margin-bottom: 4px; }
.h-salary { font-size: 13px; color: #ef4444; }
.empty { text-align: center; color: #9ca3af; font-size: 14px; padding: 20px 0; }
.btn-close { background: #f3f4f6; color: #666; padding: 12px; border-radius: 6px; font-weight: bold; border: none; cursor: pointer; width: 100%; }
</style>