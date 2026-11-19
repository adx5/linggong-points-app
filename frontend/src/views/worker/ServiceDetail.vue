<!-- frontend/src/views/worker/ServiceDetail.vue —— 大字版 P6b 同城服务详情
     结构：头图/基本信息 → 数据看板 → 服务项目 → 简介 → 平台保障 → 评价预览 → 底部预约
-->
<template>
  <div class="sd-page">
    <header class="sd-nav">
      <button class="sd-back" @click="$router.back()">‹</button>
      <span class="sd-nav-title">服务详情</span>
      <span class="sd-nav-right"></span>
    </header>

    <div v-if="loading" class="sd-tip">加载中…</div>

    <template v-else-if="profile">
      <!-- 头图与基本信息 -->
      <div class="sd-hero">
        <div class="sd-hero-bg"></div>
        <div class="sd-hero-card">
          <div class="sd-avatar">{{ (profile.display_name || '师')[0] }}</div>
          <div class="sd-hero-body">
            <h1 class="sd-name">{{ profile.display_name }}</h1>
            <p class="sd-cat">{{ profile.category_name }} · {{ profile.district }}</p>
            <div class="sd-badges">
              <span class="sd-tag">平台保障</span>
              <span class="sd-tag gray">{{ profile.verify_status === 'verified' ? '已实名认证' : '待认证' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 数据看板 -->
      <section class="sd-card stats">
        <div class="sd-stat">
          <b>{{ profile.rating }}</b><span>综合评分</span>
        </div>
        <div class="sd-stat">
          <b>{{ stats.good_rate }}%</b><span>好评率</span>
        </div>
        <div class="sd-stat">
          <b>{{ profile.orders_done }}</b><span>累计接单</span>
        </div>
      </section>

      <!-- 服务项目 -->
      <section class="sd-card">
        <h2 class="sd-h2">服务项目</h2>
        <div v-if="services.length" class="sd-items">
          <div v-for="s in services" :key="s.id" class="sd-item">
            <div class="sd-item-main">
              <span class="sd-item-name">{{ s.title }}</span>
              <span v-if="s.description" class="sd-item-desc">{{ s.description }}</span>
            </div>
            <span class="sd-item-price">￥{{ s.price }}<small>/{{ s.price_unit }}</small></span>
          </div>
        </div>
        <p v-else class="sd-text">该师傅暂未上架服务，可先在线咨询或直接预约。</p>
      </section>

      <!-- 简介 -->
      <section class="sd-card">
        <h2 class="sd-h2">服务简介</h2>
        <p class="sd-text">{{ profile.intro || '暂无简介' }}</p>
      </section>

      <!-- 平台保障 -->
      <section class="sd-card warn">
        <h2 class="sd-h2">平台保障与声明</h2>
        <p class="sd-text">
          平台仅提供信息撮合，不参与线下交易与收款。请勿向师傅私下转账，务必在平台内完成预约；
          出现纠纷可通过「我的订单」发起申诉。
        </p>
      </section>

      <!-- 评价预览 -->
      <section class="sd-card">
        <div class="sd-h2-row">
          <h2 class="sd-h2">用户评价（{{ stats.total_reviews }}）</h2>
          <span class="sd-more" @click="goReviews">全部 ›</span>
        </div>
        <div v-if="recent.length">
          <div v-for="r in recent" :key="r.id" class="sd-review">
            <div class="sd-review-head">
              <span class="sd-review-user">{{ r.customer_name }}</span>
              <span class="sd-stars">{{ '★'.repeat(r.rating) }}</span>
            </div>
            <p class="sd-review-text">{{ r.content }}</p>
            <span class="sd-review-date">{{ r.created_at }}</span>
          </div>
        </div>
        <p v-else class="sd-text">暂无评价</p>
      </section>

      <div class="sd-space"></div>

      <div class="sd-action">
        <button class="sd-btn ghost" @click="contact">咨询</button>
        <button class="sd-btn primary" :disabled="submitting" @click="book">
          {{ submitting ? '提交中…' : '立即预约' }}
        </button>
      </div>
    </template>

    <div v-else class="sd-tip">服务商不存在</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const submitting = ref(false)
const profile = ref(null)
const stats = ref({ total_reviews: 0, good_rate: 100, distribution: { 5: 0, 4: 0, 3: 0 } })
const recent = ref([])
const services = ref([])

const isLogged = () => !!localStorage.getItem('token')

async function load() {
  loading.value = true
  try {
    const res = await api.get(`/services/providers/${route.params.id}`)
    profile.value = res.data.profile
    stats.value = res.data.stats || stats.value
    recent.value = res.data.recent_reviews || []
    services.value = res.data.services || []
  } catch (err) {
    profile.value = null
    if (window.$toast) window.$toast(err.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

function goReviews() {
  router.push(`/worker/service-reviews/${route.params.id}`)
}

async function contact() {
  if (!isLogged()) {
    window.$toast && window.$toast('登录后即可咨询')
    return router.push({ path: '/login', query: { role: 'worker', redirect: route.fullPath } })
  }
  if (!window.confirm(`向「${profile.value.display_name}」发起上门评估预约？`)) return

  submitting.value = true
  try {
    await api.post('/services/orders', {
      provider_profile_id: profile.value.id,
      title: `${profile.value.category_name} 上门评估`,
      description: '用户从服务详情页发起咨询'
    })
    window.$toast && window.$toast('已发起预约，师傅会尽快联系你')
  } catch (err) {
    window.$toast && window.$toast(err.response?.data?.detail || '发起失败')
  } finally {
    submitting.value = false
  }
}

async function book() {
  if (!isLogged()) {
    window.$toast && window.$toast('登录后即可预约')
    return router.push({
      path: '/login',
      query: { role: 'worker', redirect: route.fullPath }
    })
  }
  submitting.value = true
  try {
    const res = await api.post('/services/orders', {
      provider_profile_id: profile.value.id,
      title: `${profile.value.category_name} 上门服务`,
      description: '用户从服务详情页发起预约',
      address: '',
      scheduled_at: ''
    })
    window.$toast && window.$toast(res.message || '预约成功，等待师傅联系')
    setTimeout(() => router.push('/worker/mine'), 1200)
  } catch (err) {
    const status = err.response?.status
    const detail = err.response?.data?.detail || '预约失败'
    window.$toast && window.$toast(detail)
    if (status === 403 && String(detail).includes('C 端')) {
      router.push({ path: '/login', query: { role: 'worker', redirect: route.fullPath } })
    }
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.sd-page { min-height:100vh; background:var(--bg, #eef1f5); font-family:'PingFang SC','Microsoft YaHei',sans-serif; }

.sd-nav { position:sticky; top:0; z-index:20; height:52px; background:#fff; display:flex; align-items:center; padding:0 12px; box-shadow:0 2px 8px rgba(0,0,0,.03); }
.sd-back { border:none; background:none; font-size:30px; line-height:1; color:#333; width:40px; text-align:left; padding-bottom:6px; }
.sd-nav-title { flex:1; text-align:center; font-size:18px; font-weight:800; color:#111; }
.sd-nav-right { width:40px; }

.sd-hero { position:relative; }
.sd-hero-bg { height:120px; background:linear-gradient(140deg,#ffd6b0,#ff9a4d); }
.sd-hero-card {
  position:relative; margin:-56px 20px 0; background:#fff; border-radius:18px;
  padding:16px; display:flex; gap:14px; box-shadow:0 8px 24px rgba(31,79,143,.10);
}
.sd-avatar { width:64px; height:64px; border-radius:18px; background:linear-gradient(135deg,#ffb27a,#ff8a2b); color:#fff; font-size:26px; font-weight:800; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.sd-hero-body { flex:1; min-width:0; }
.sd-name { font-size:22px; font-weight:800; color:#111; }
.sd-cat { font-size:13px; color:#7b8797; margin:4px 0 8px; }
.sd-badges { display:flex; gap:8px; }
.sd-tag { background:var(--brand-soft); color:var(--brand); font-size:12px; font-weight:700; padding:3px 9px; border-radius:6px; }
.sd-tag.gray { background:var(--bg); color:#555; }

.sd-card { background:#fff; border-radius:16px; padding:18px 20px; margin:12px 20px 0; box-shadow:0 4px 12px rgba(0,0,0,.04); }
.sd-card.warn { background:#fffaf3; border:1px solid #ffe3cc; }
.sd-card.stats { display:flex; justify-content:space-around; }
.sd-stat { display:flex; flex-direction:column; align-items:center; gap:4px; }
.sd-stat b { font-size:22px; font-weight:800; color:var(--brand); }
.sd-stat span { font-size:12px; color:#7b8797; }

.sd-h2 { font-size:18px; font-weight:800; color:#111; margin-bottom:12px; }
.sd-h2-row { display:flex; align-items:baseline; justify-content:space-between; }
.sd-more { font-size:14px; color:#7b8797; }
.sd-text { font-size:15px; color:#4a5565; line-height:1.7; }

.sd-items { display:flex; flex-direction:column; }
.sd-item { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:14px 0; border-bottom:1px solid #f2f4f7; }
.sd-item:last-child { border-bottom:none; }
.sd-item-main { flex:1; min-width:0; display:flex; flex-direction:column; gap:4px; }
.sd-item-name { font-size:16px; font-weight:700; color:#333; }
.sd-item-desc { font-size:12px; color:#9aa6b5; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.sd-item-price { flex-shrink:0; font-size:17px; font-weight:800; color:var(--brand); }
.sd-item-price small { font-size:12px; }

.sd-review { padding:12px 0; border-bottom:1px solid #f2f4f7; }
.sd-review:last-child { border-bottom:none; }
.sd-review-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; }
.sd-review-user { font-size:14px; font-weight:700; color:#333; }
.sd-stars { color:#ffb020; font-size:13px; }
.sd-review-text { font-size:14px; color:#4a5565; line-height:1.6; }
.sd-review-date { font-size:12px; color:#9aa6b5; }

.sd-space { height:120px; }
.sd-action { position:fixed; left:0; right:0; bottom:60px; display:flex; gap:12px; padding:10px 20px 12px; background:#fff; border-top:1px solid #eef0f3; z-index:15; }
.sd-btn { border:none; height:50px; border-radius:12px; font-size:17px; font-weight:800; }
.sd-btn.ghost { width:104px; background:var(--bg); color:#555; }
.sd-btn.primary { flex:1; background:var(--brand); color:#fff; }
.sd-btn.primary:disabled { opacity:.6; }

.sd-tip { text-align:center; color:#9aa6b5; font-size:15px; padding:60px 0; }
</style>
