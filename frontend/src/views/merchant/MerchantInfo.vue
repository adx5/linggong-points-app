<!-- (B端企业信息维护：公开信息) -->
<template>
  <div class="info-page">
    <div class="sticky-header">
      <div class="header-left">
        <div class="btn-back" @click="$router.back()">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#1f2937" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
        </div>
        <h2>基本信息维护</h2>
      </div>
    </div>

    <div class="content">
      <div class="form-box">
        <div class="form-item">
          <label>企业名称 / 门店名称</label>
          <input v-model="form.company_name" placeholder="请填写真实企业名称" />
        </div>

        <div class="form-item">
          <label>所属行业</label>
          <div class="tag-list">
            <div v-for="tag in baseIndustries" :key="tag" class="tag-btn" :class="{ active: form.industry === tag }" @click="form.industry = tag">
              {{ tag }}
            </div>
          </div>
        </div>

        <div class="form-item">
          <label>企业简介 <span class="label-tip">(限100字)</span></label>
          <textarea v-model="form.intro" placeholder="如：XX连锁超市，环境好；或 XX电子厂，包吃住..." rows="3" maxlength="100"></textarea>
          <div class="word-count">{{ form.intro.length }}/100</div>
        </div>

        <div class="form-item">
          <label>工作地点</label>
          <div class="address-select-row">
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
          <div class="address-row" style="margin-top: 8px;">
            <input v-model="form.address_detail" placeholder="请输入详细街道、门牌号" style="flex:1;" />
          </div>
        </div>

        <div class="form-item">
          <label>对外联系电话</label>
          <input v-model="form.contact_phone" type="tel" placeholder="手机号/座机" />
        </div>
      </div>

      <div class="bottom-bar">
        <button class="btn-save" @click="saveInfo">保存修改</button>
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
  company_name: '',
  industry: '制造加工',
  intro: '',
  province: '',
  city: '',
  district: '',
  address_detail: '',
  contact_phone: ''
})

const baseIndustries = ['制造加工', '餐饮', '物流', '零售', '物业', '其他']

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

// 🚨 进入页面时回显真实数据
onMounted(async () => {
  try {
    const res = await api.get('/merchant/info')
    if (res.data) {
      form.company_name = res.data.name || ''
      if (res.data.ext_info) {
        form.industry = res.data.ext_info.industry || '制造加工'
        form.intro = res.data.ext_info.intro || ''
        form.province = res.data.ext_info.province || ''
        form.city = res.data.ext_info.city || ''
        form.district = res.data.ext_info.district || ''
        form.address_detail = res.data.ext_info.address_detail || ''
        form.contact_phone = res.data.ext_info.contact_phone || ''
      }
    }
  } catch (err) { console.error(err) }
})

const saveInfo = async () => {
  if (!form.company_name || form.company_name === '请完善名称') {
    return window.$toast('请填写真实的企业名称')
  }

  const payload = {
    company_name: form.company_name,
    industry: form.industry,
    intro: form.intro,
    province: form.province,
    city: form.city,
    district: form.district,
    address_detail: form.address_detail,
    contact_phone: form.contact_phone,
    // 传空占位，防止 Pydantic 报错
    cover_image: "", intro_images: "", landmark: "", phone_time: "09:00-18:00"
  }

  try {
    await api.put('/merchant/info', payload)
    window.$toast('保存成功')
    setTimeout(() => { router.back() }, 1000)
  } catch (err) {
    window.$toast('保存失败，请检查网络')
  }
}
</script>

<style scoped>
.info-page { min-height: 100vh; background: #f0f2f5; padding-bottom: 80px; }
.sticky-header { position: sticky; top: 0; z-index: 99; background: #fff; padding: 16px; border-bottom: 1px solid #eee; }
.header-left { display: flex; align-items: center; gap: 8px; }
.btn-back { cursor: pointer; display: flex; align-items: center; margin-left: -8px; }
.sticky-header h2 { font-size: 18px; color: #1f2937; }
.content { padding: 16px; }
.form-box { background: #fff; border-radius: 12px; padding: 16px; }
.form-item { margin-bottom: 20px; position: relative; }
.form-item label { display: block; font-size: 14px; font-weight: bold; color: #333; margin-bottom: 8px; }
.label-tip { font-weight: normal; font-size: 12px; color: #9ca3af; }
.form-item input, .form-item textarea, .form-item select { width: 100%; padding: 10px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; outline: none; background: #f9fafb; }
.form-item input:focus, .form-item textarea:focus, .form-item select:focus { border-color: #2563eb; background: #fff; }
.form-item textarea { resize: none; }
.tag-list { display: flex; flex-wrap: wrap; gap: 8px; }
.tag-btn { padding: 6px 12px; background: #f3f4f6; color: #4b5563; border-radius: 6px; font-size: 13px; cursor: pointer; border: 1px solid transparent; }
.tag-btn.active { background: #eff6ff; color: #2563eb; border-color: #2563eb; font-weight: bold; }
.word-count { position: absolute; right: 10px; bottom: 8px; font-size: 12px; color: #9ca3af; }
.address-select-row { display: flex; gap: 8px; margin-bottom: 8px; }
.address-select-row select { flex: 1; }
.address-row { display: flex; gap: 8px; }
.bottom-bar { position: fixed; bottom: 0; left: 0; right: 0; padding: 12px 16px; background: #fff; box-shadow: 0 -2px 10px rgba(0,0,0,0.05); z-index: 100; }
.btn-save { width: 100%; background: #2563eb; color: #fff; padding: 12px; border-radius: 8px; font-size: 16px; font-weight: bold; border: none; cursor: pointer; }
</style>