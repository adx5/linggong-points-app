<!-- frontend/src/views/merchant/MerchantVerify.vue (B端我的备案：图片压缩真实上传) -->
<template>
  <div class="verify-page">
    <div class="sticky-header">
      <div class="header-left">
        <div class="btn-back" @click="$router.back()">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#1f2937" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
        </div>
        <h2>企业用工备案登记</h2>
      </div>
    </div>

    <div class="content">
      <div class="status-banner status-none" v-if="rejectReason">
        <span class="icon">❌</span>
        <div class="text">
          <h3>审核驳回</h3>
          <p>驳回原因：{{ rejectReason }}<br>请修改下方信息后重新提交。</p>
        </div>
      </div>

      <div class="form-box">
        <div class="form-item">
          <label>企业营业执照</label>
          <div class="upload-box" @click="triggerUpload('license')">
            <span v-if="!form.license_img">点击上传营业执照副本</span>
            <img v-else :src="form.license_img" alt="营业执照" />
          </div>
          <input type="file" ref="licenseInput" accept="image/*,application/pdf" style="display: none;" @change="handleFileChange($event, 'license_img')" />
        </div>

        <div class="form-item">
          <label>统一社会信用代码</label>
          <input v-model="form.credit_code" placeholder="请输入18位信用代码" maxlength="18" />
        </div>

        <div class="form-item">
          <label>招聘负责人姓名</label>
          <input v-model="form.contact_name" placeholder="请输入真实姓名" />
        </div>

        <div class="form-item">
          <label>负责人身份证（正反面）</label>
          <div class="id-card-row">
            <div class="upload-box small" @click="triggerUpload('id_front')">
              <span v-if="!form.id_front">身份证正面</span>
              <img v-else :src="form.id_front" alt="正面" />
            </div>
            <div class="upload-box small" @click="triggerUpload('id_back')">
              <span v-if="!form.id_back">身份证反面</span>
              <img v-else :src="form.id_back" alt="反面" />
            </div>
          </div>
          <input type="file" ref="idFrontInput" accept="image/*" style="display: none;" @change="handleFileChange($event, 'id_front')" />
          <input type="file" ref="idBackInput" accept="image/*" style="display: none;" @change="handleFileChange($event, 'id_back')" />
        </div>

        <div class="form-item">
          <label>实名手机号</label>
          <input v-model="form.contact_phone" type="tel" placeholder="请输入手机号" maxlength="11" />
        </div>
      </div>

      <div class="bottom-bar">
        <button class="btn-submit" @click="submitVerify" :disabled="uploading">
          {{ uploading ? '正在上传中...' : '提交审核' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
import imageCompression from 'browser-image-compression'

const router = useRouter()
const rejectReason = ref('')
const uploading = ref(false)

const form = reactive({
  license_img: '', credit_code: '', contact_name: '', id_front: '', id_back: '', contact_phone: ''
})

const licenseInput = ref(null)
const idFrontInput = ref(null)
const idBackInput = ref(null)

onMounted(async () => {
  try {
    const res = await api.get('/merchant/info')
    if (res.data) {
      rejectReason.value = res.data.reject_reason || ''
      if (res.data.ext_info) {
        form.license_img = res.data.ext_info.license_img || ''
        form.credit_code = res.data.ext_info.credit_code || ''
        form.contact_name = res.data.ext_info.contact_name || ''
        form.id_front = res.data.ext_info.id_front || ''
        form.id_back = res.data.ext_info.id_back || ''
        form.contact_phone = res.data.ext_info.contact_phone || ''
      }
    }
  } catch (err) { console.error(err) }
})

const triggerUpload = (type) => {
  if (type === 'license') licenseInput.value.click()
  if (type === 'id_front') idFrontInput.value.click()
  if (type === 'id_back') idBackInput.value.click()
}

const handleFileChange = async (event, type) => {
  const file = event.target.files[0]
  if (!file) return

  const isPdf = file.type === 'application/pdf'
  if (isPdf && type !== 'license_img') {
    return window.$toast('身份证仅支持图片格式')
  }

  uploading.value = true
  try {
    let uploadFile = file
    if (!isPdf) {
      const options = { maxSizeMB: 0.2, maxWidthOrHeight: 1920, useWebWorker: true, fileType: 'image/jpeg' }
      try {
        uploadFile = await imageCompression(file, options)
      } catch (error) {
        window.$toast('图片压缩失败，尝试直接上传')
      }
    } else {
      if (file.size > 2 * 1024 * 1024) return window.$toast('PDF 文件不能超过 2MB')
    }

    const formData = new FormData()
    formData.append('file', uploadFile)
    const res = await api.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    form[type] = res.url
    window.$toast('上传成功')
  } catch (err) {
    window.$toast(err.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
    event.target.value = ''
  }
}

const submitVerify = async () => {
  if (!form.credit_code || !form.contact_name || !form.contact_phone) return window.$toast('请填写完整的备案信息')
  if (!form.license_img) return window.$toast('请上传营业执照')

  try {
    const res = await api.post('/merchant/verify', form)
    window.$toast(res.message || '资料已提交，等待平台审核')
    setTimeout(() => { router.back() }, 1500)
  } catch (err) {
    window.$toast('提交失败，请检查网络')
  }
}
</script>

<style scoped>
.verify-page { min-height: 100vh; background: #f0f2f5; padding-bottom: 80px; }
.sticky-header { position: sticky; top: 0; z-index: 99; background: #fff; padding: 16px; border-bottom: 1px solid #eee; }
.header-left { display: flex; align-items: center; gap: 8px; }
.btn-back { cursor: pointer; display: flex; align-items: center; margin-left: -8px; }
.sticky-header h2 { font-size: 18px; color: #1f2937; font-weight: bold; }
.content { padding: 16px; }
.status-banner { display: flex; gap: 12px; padding: 16px; border-radius: 12px; margin-bottom: 16px; background: #fef2f2; color: #b91c1c; }
.status-banner .icon { font-size: 24px; }
.status-banner .text h3 { font-size: 16px; font-weight: bold; margin-bottom: 4px; }
.status-banner .text p { font-size: 13px; line-height: 1.5; }
.form-box { background: #fff; border-radius: 12px; padding: 16px; }
.form-item { margin-bottom: 20px; }
.form-item label { display: block; font-size: 14px; font-weight: bold; color: #333; margin-bottom: 8px; }
.form-item input { width: 100%; padding: 10px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; outline: none; background: #f9fafb; }
.form-item input:focus { border-color: #2563eb; background: #fff; }
.upload-box { width: 100%; height: 120px; border: 1px dashed #d1d5db; border-radius: 8px; background: #f9fafb; display: flex; justify-content: center; align-items: center; color: #9ca3af; font-size: 13px; cursor: pointer; overflow: hidden; }
.upload-box img { width: 100%; height: 100%; object-fit: contain; }
.id-card-row { display: flex; gap: 12px; }
.upload-box.small { flex: 1; height: 90px; }
.bottom-bar { position: fixed; bottom: 0; left: 0; right: 0; padding: 12px 16px; background: #fff; box-shadow: 0 -2px 10px rgba(0,0,0,0.05); padding-bottom: env(safe-area-inset-bottom); z-index: 100; }
.btn-submit { width: 100%; background: #10b981; color: #fff; padding: 12px; border-radius: 8px; font-size: 16px; font-weight: bold; border: none; cursor: pointer; }
.btn-submit:disabled { background: #a7f3d0; }
</style>