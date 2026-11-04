<!-- frontend/src/views/worker/WorkerVerify.vue (C端实名认证：修复上传路径) -->
<template>
  <div class="verify-page">
    <div class="sticky-header">
      <div class="header-left">
        <div class="btn-back" @click="$router.back()">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#1f2937" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
        </div>
        <h2>个人信息认证</h2>
      </div>
    </div>

    <div class="content">
      <div v-if="status === 'verified'" class="success-banner">
        <span class="icon">✅</span>
        <div class="text">
          <h3>已完成实名认证</h3>
          <p>姓名：{{ realName }}</p>
          <p>您的身份已通过核验，可安心投递岗位。</p>
        </div>
      </div>

      <div v-else class="form-box">
        <div class="tips-box">
          根据平台合规要求，投递简历前需完成实名认证。您的信息将被严格加密保护。
        </div>

        <div class="form-item">
          <label>真实姓名</label>
          <input v-model="form.real_name" placeholder="请输入真实姓名" />
        </div>

        <div class="form-item">
          <label>身份证号</label>
          <input v-model="form.id_card" placeholder="请输入18位身份证号" maxlength="18" />
        </div>

        <div class="form-item">
          <label>身份证正反面</label>
          <div class="id-card-row">
            <div class="upload-box small" @click="triggerUpload('id_front_img')">
              <span v-if="!form.id_front_img">身份证正面</span>
              <img v-else :src="form.id_front_img" alt="正面" />
            </div>
            <div class="upload-box small" @click="triggerUpload('id_back_img')">
              <span v-if="!form.id_back_img">身份证反面</span>
              <img v-else :src="form.id_back_img" alt="反面" />
            </div>
          </div>
          <input type="file" ref="idFrontInput" accept="image/*" style="display: none;" @change="handleFileChange($event, 'id_front_img')" />
          <input type="file" ref="idBackInput" accept="image/*" style="display: none;" @change="handleFileChange($event, 'id_back_img')" />
        </div>

        <div class="submit-section">
          <button class="btn-submit" @click="submitVerify" :disabled="uploading">
            {{ uploading ? '提交中...' : '提交认证' }}
          </button>
        </div>
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
const status = ref('unverified')
const realName = ref('')
const uploading = ref(false)

const form = reactive({
  real_name: '', id_card: '', id_front_img: '', id_back_img: ''
})

const idFrontInput = ref(null)
const idBackInput = ref(null)

onMounted(async () => {
  try {
    const res = await api.get('/user/verify-status')
    status.value = res.data.status
    realName.value = res.data.real_name
  } catch (err) { console.error(err) }
})

const triggerUpload = (type) => {
  if (type === 'id_front_img') idFrontInput.value.click()
  if (type === 'id_back_img') idBackInput.value.click()
}

const handleFileChange = async (event, type) => {
  const file = event.target.files[0]
  if (!file) return

  uploading.value = true
  try {
    const options = { maxSizeMB: 0.2, maxWidthOrHeight: 1920, useWebWorker: true, fileType: 'image/jpeg' }
    const uploadFile = await imageCompression(file, options)

    const formData = new FormData()
    formData.append('file', uploadFile)

    // 🚨 核心修复：路径必须是 /upload/verify
    const res = await api.post('/upload/verify', formData, { headers: { 'Content-Type': 'multipart/form-data' } })

    form[type] = res.data.url
    window.$toast('上传成功')
  } catch (err) {
    window.$toast(err.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
    event.target.value = ''
  }
}

const submitVerify = async () => {
  if (!form.real_name || !form.id_card || !form.id_front_img || !form.id_back_img) {
    return window.$toast('请填写完整信息并上传身份证照片')
  }
  if (form.id_card.length !== 18) return window.$toast('身份证号必须为18位')

  uploading.value = true
  try {
    await api.post('/user/verify', form)
    window.$toast('实名认证成功')
    setTimeout(() => { router.back() }, 1000)
  } catch (err) {
    window.$toast(err.response?.data?.detail || '认证失败')
  } finally {
    uploading.value = false
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
.success-banner { display: flex; gap: 12px; padding: 20px; border-radius: 12px; background: #ecfdf5; color: #10b981; border: 1px solid #a7f3d0; }
.success-banner .icon { font-size: 32px; }
.success-banner .text h3 { font-size: 18px; font-weight: bold; margin-bottom: 8px; }
.success-banner .text p { font-size: 14px; margin-bottom: 4px; }
.form-box { background: #fff; border-radius: 12px; padding: 16px; }
.tips-box { background: #eff6ff; color: #2563eb; font-size: 13px; padding: 12px; border-radius: 8px; margin-bottom: 20px; line-height: 1.5; }
.form-item { margin-bottom: 20px; }
.form-item label { display: block; font-size: 14px; font-weight: bold; color: #333; margin-bottom: 8px; }
.form-item input { width: 100%; box-sizing: border-box; padding: 12px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; outline: none; background: #f9fafb; }
.form-item input:focus { border-color: #2563eb; background: #fff; }
.upload-box { width: 100%; height: 120px; border: 1px dashed #d1d5db; border-radius: 8px; background: #f9fafb; display: flex; justify-content: center; align-items: center; color: #9ca3af; font-size: 13px; cursor: pointer; overflow: hidden; }
.upload-box img { width: 100%; height: 100%; object-fit: contain; }
.id-card-row { display: flex; gap: 12px; }
.upload-box.small { flex: 1; height: 100px; }
.submit-section { margin-top: 30px; margin-bottom: 20px; }
.btn-submit { width: 100%; background: #10b981; color: #fff; padding: 14px; border-radius: 8px; font-size: 16px; font-weight: bold; border: none; cursor: pointer; }
.btn-submit:disabled { background: #a7f3d0; }
</style>