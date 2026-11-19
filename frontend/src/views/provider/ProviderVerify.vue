<!-- frontend/src/views/provider/ProviderVerify.vue —— 资质与实名认证 -->
<template>
  <div class="pv-page">
    <div class="pv-tip">
      <span class="pv-check">✓</span>
      <div>
        <div class="pv-tip-title">认证越全，接单越多</div>
        <div class="pv-tip-sub">完成实名和技能认证后，客户搜索时您的服务将优先展示。</div>
      </div>
    </div>

    <section class="pv-card">
      <div class="pv-card-head">
        <h2>实名认证</h2>
        <span :class="['pv-badge', verified ? 'ok' : 'warn']">{{ verified ? '已通过' : '未认证' }}</span>
      </div>
      <div class="pv-id-box">
        <div>
          <div class="pv-name">{{ realName || '未填写' }}</div>
          <div class="pv-id">{{ idMasked || '身份证：—' }}</div>
        </div>
        <div class="pv-stamp">{{ verified ? '已核验' : '待核验' }}</div>
      </div>
      <button v-if="!verified" class="pv-primary" @click="goVerify">去完成实名认证</button>
    </section>

    <section class="pv-card">
      <div class="pv-card-head">
        <h2>技能证书</h2>
        <span class="pv-count">已认证 {{ certs.length }} 项</span>
      </div>

      <div v-for="c in certs" :key="c.id" class="pv-cert">
        <div class="pv-cert-left">
          <div class="pv-cert-icon">
            <img v-if="c.image_url" :src="c.image_url" class="pv-cert-img" alt="" />
            <span v-else>证</span>
          </div>
          <div>
            <div class="pv-cert-name">{{ c.title }}</div>
            <div :class="['pv-cert-status', c.status]">{{ statusText(c.status) }}</div>
          </div>
        </div>
        <a v-if="c.image_url" :href="c.image_url" target="_blank" rel="noopener" class="pv-cert-more">查看 ›</a>
      </div>

      <p v-if="!certs.length" class="pv-empty">暂无证书，上传后可提升客户信任</p>

      <input ref="fileInput" type="file" accept="image/*" class="pv-file" @change="onFile" />
      <button class="pv-upload" :disabled="uploading" @click="pickFile">
        {{ uploading ? '上传中…' : '+ 点击拍照，上传新证书' }}
      </button>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import imageCompression from 'browser-image-compression'
import api from '../../api'

const router = useRouter()

const verified = ref(false)
const realName = ref('')
const idMasked = ref('')
const certs = ref([])

const fileInput = ref(null)
const uploading = ref(false)

const STATUS_TEXT = { pending: '待平台核验', verified: '平台已核验', rejected: '核验未通过' }
function statusText(s) {
  return STATUS_TEXT[s] || '待平台核验'
}

async function load() {
  try {
    const res = await api.get('/user/profile')
    verified.value = res.data?.verify_status === 'verified'
    realName.value = res.data?.real_name || ''
    idMasked.value = res.data?.id_card_masked
      ? `身份证：${res.data.id_card_masked}`
      : ''
  } catch (err) {}

  await loadCerts()
}

async function loadCerts() {
  try {
    const res = await api.get('/services/my-certificates')
    certs.value = res.data || []
  } catch (err) {
    certs.value = []
  }
}

function goVerify() {
  router.push('/worker/verify')
}

function pickFile() {
  if (uploading.value) return
  fileInput.value && fileInput.value.click()
}

async function onFile(event) {
  const file = event.target.files && event.target.files[0]
  event.target.value = ''
  if (!file) return

  const title = window.prompt('给这张证书起个名字', '技能证书')
  if (title === null) return

  uploading.value = true
  try {
    // 与 C 端一致：先压缩再上传，避免手机原图超限
    let uploadFile = file
    try {
      uploadFile = await imageCompression(file, {
        maxSizeMB: 0.2,
        maxWidthOrHeight: 1920,
        useWebWorker: true,
        fileType: 'image/jpeg'
      })
    } catch (err) {
      // 压缩失败就直接传原图，交给后端校验
    }

    const formData = new FormData()
    formData.append('file', uploadFile)

    // 走项目已有图床（BeeIMG）
    const up = await api.post('/upload/normal', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    const imageUrl = up.data?.url
    if (!imageUrl) throw new Error('图床未返回地址')

    await api.post('/services/my-certificates', {
      title: (title || '技能证书').trim() || '技能证书',
      image_url: imageUrl
    })

    window.$toast && window.$toast('证书已提交，等待平台审核')
    await loadCerts()
  } catch (err) {
    window.$toast && window.$toast(err.response?.data?.detail || '上传失败，请重试')
  } finally {
    uploading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.pv-page { min-height: 100vh; background: var(--bg); padding: 16px 20px 40px; }

.pv-tip {
  display: flex;
  gap: 12px;
  background: var(--g-soft);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 18px;
}
.pv-check { font-size: 22px; color: var(--g); font-weight: 800; line-height: 1.1; }
.pv-tip-title { font-size: 16px; font-weight: 800; color: var(--g-text); margin-bottom: 4px; }
.pv-tip-sub { font-size: 13px; color: var(--g); line-height: 1.5; }

.pv-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}
.pv-card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.pv-card-head h2 { font-size: 18px; font-weight: 800; color: var(--text); }
.pv-badge { font-size: 13px; font-weight: 800; padding: 4px 8px; border-radius: 4px; }
.pv-badge.ok { color: var(--g-text); background: var(--g-soft); }
.pv-badge.warn { color: var(--warn); background: var(--warn-soft); }
.pv-count { font-size: 13px; color: #7b8797; }

.pv-id-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f9fafc;
  border-radius: 12px;
  padding: 16px;
}
.pv-name { font-size: 18px; font-weight: 800; color: #333; margin-bottom: 4px; }
.pv-id { font-size: 14px; color: #666; }
.pv-stamp {
  width: 66px;
  height: 44px;
  border-radius: 6px;
  background: #e5e6eb;
  color: #999;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.pv-primary {
  margin-top: 16px;
  width: 100%;
  height: 50px;
  border: none;
  border-radius: 12px;
  background: var(--g);
  color: #fff;
  font-size: 17px;
  font-weight: 800;
}

.pv-cert {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f9fafc;
  border: 1px solid #ebecf0;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}
.pv-cert-left { display: flex; align-items: center; gap: 12px; }
.pv-cert-icon {
  width: 40px; height: 40px; border-radius: 8px;
  background: var(--g-soft); color: var(--g-text);
  display: flex; align-items: center; justify-content: center;
  font-weight: 800;
  overflow: hidden;
  flex-shrink: 0;
}
.pv-cert-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.pv-cert-name { font-size: 16px; font-weight: 800; color: var(--text); }
.pv-cert-status { font-size: 13px; color: var(--g-text); margin-top: 2px; }
.pv-cert-status.pending { color: var(--warn); }
.pv-cert-status.rejected { color: var(--danger); }
.pv-cert-more { font-size: 14px; color: #666; text-decoration: none; flex-shrink: 0; }
.pv-empty { text-align: center; color: #9aa6b5; font-size: 14px; padding: 12px 0; }

.pv-file { display: none; }

.pv-upload {
  margin-top: 12px;
  width: 100%;
  height: 54px;
  border-radius: 12px;
  border: 2px dashed var(--g);
  background: var(--g-soft);
  color: var(--g-text);
  font-size: 16px;
  font-weight: 800;
}
.pv-upload:disabled { opacity: 0.6; }
</style>
