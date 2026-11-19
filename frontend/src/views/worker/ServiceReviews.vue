<!-- frontend/src/views/worker/ServiceReviews.vue —— 大字版 P6c 服务评价列表
     结构：商家信息 + 评分总览(星级分布) + 评价列表
-->
<template>
  <div class="sr-page">
    <header class="sr-nav">
      <button class="sr-back" @click="$router.back()">‹</button>
      <span class="sr-nav-title">全部评价</span>
      <span class="sr-nav-right"></span>
    </header>

    <div v-if="loading" class="sr-tip">加载中…</div>

    <template v-else>
      <!-- 商家 + 评分总览 -->
      <section class="sr-card">
        <div class="sr-shop">
          <div class="sr-avatar">{{ (profile.display_name || '师')[0] }}</div>
          <div class="sr-shop-body">
            <h3 class="sr-shop-name">{{ profile.display_name }}</h3>
            <p class="sr-shop-sub">{{ profile.category_name }} · {{ profile.district }}</p>
          </div>
          <div class="sr-score">
            <b>{{ profile.rating }}</b>
            <span>综合分</span>
          </div>
        </div>

        <div class="sr-bars">
          <div v-for="row in distributionRows" :key="row.star" class="sr-bar-row">
            <span class="sr-bar-label">{{ row.label }}</span>
            <div class="sr-bar-track">
              <div class="sr-bar-fill" :style="{ width: row.percent + '%' }"></div>
            </div>
            <span class="sr-bar-num">{{ row.count }}</span>
          </div>
        </div>

        <div class="sr-extra">
          <span>累计评价 <b>{{ stats.total_reviews }}</b> 条</span>
          <span>好评率 <b>{{ stats.good_rate }}%</b></span>
        </div>
      </section>

      <!-- 评价列表 -->
      <section class="sr-list">
        <article v-for="r in reviews" :key="r.id" class="sr-item">
          <div class="sr-item-head">
            <span class="sr-user">{{ r.customer_name }}</span>
            <span class="sr-stars">{{ '★'.repeat(r.rating) }}</span>
          </div>
          <p class="sr-content">{{ r.content }}</p>
          <div v-if="r.images && r.images.length" class="sr-imgs">
            <img v-for="(img, i) in r.images" :key="i" :src="img" class="sr-img" alt="" />
          </div>
          <span class="sr-date">{{ r.created_at }}</span>
        </article>

        <p v-if="!reviews.length" class="sr-tip">还没有评价</p>
        <p v-else class="sr-tip">— 已经到底了 —</p>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../api'

const route = useRoute()

const loading = ref(true)
const profile = ref({})
const stats = ref({ total_reviews: 0, good_rate: 100, distribution: { 5: 0, 4: 0, 3: 0 } })
const reviews = ref([])

const distributionRows = computed(() => {
  const d = stats.value.distribution || {}
  const total = stats.value.total_reviews || 0
  const rows = [
    { star: 5, label: '5 星', count: d['5'] || d[5] || 0 },
    { star: 4, label: '4 星', count: d['4'] || d[4] || 0 },
    { star: 3, label: '3 星及以下', count: d['3'] || d[3] || 0 }
  ]
  return rows.map((r) => ({ ...r, percent: total ? Math.round(r.count / total * 100) : 0 }))
})

async function load() {
  loading.value = true
  try {
    const detail = await api.get(`/services/providers/${route.params.id}`)
    profile.value = detail.data.profile
    stats.value = detail.data.stats || stats.value

    const list = await api.get(`/services/providers/${route.params.id}/reviews`, { params: { page: 1, size: 30 } })
    reviews.value = list.data || []
  } catch (err) {
    reviews.value = []
    if (window.$toast) window.$toast(err.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.sr-page { min-height:100vh; background:var(--bg, #eef1f5); padding-bottom:24px; font-family:'PingFang SC','Microsoft YaHei',sans-serif; }

.sr-nav { position:sticky; top:0; z-index:20; height:52px; background:#fff; display:flex; align-items:center; padding:0 12px; box-shadow:0 2px 8px rgba(0,0,0,.03); }
.sr-back { border:none; background:none; font-size:30px; line-height:1; color:#333; width:40px; text-align:left; padding-bottom:6px; }
.sr-nav-title { flex:1; text-align:center; font-size:18px; font-weight:800; color:#111; }
.sr-nav-right { width:40px; }

.sr-card { background:#fff; border-radius:16px; padding:18px 20px; margin:12px 20px 0; box-shadow:0 4px 12px rgba(0,0,0,.04); }

.sr-shop { display:flex; align-items:center; gap:12px; }
.sr-avatar { width:56px; height:56px; border-radius:16px; background:linear-gradient(135deg,#ffb27a,#ff8a2b); color:#fff; font-size:24px; font-weight:800; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.sr-shop-body { flex:1; min-width:0; }
.sr-shop-name { font-size:19px; font-weight:800; color:#111; }
.sr-shop-sub { font-size:13px; color:#7b8797; margin-top:3px; }
.sr-score { text-align:center; }
.sr-score b { display:block; font-size:26px; font-weight:800; color:var(--brand); line-height:1.1; }
.sr-score span { font-size:12px; color:#7b8797; }

.sr-bars { margin-top:16px; display:flex; flex-direction:column; gap:10px; }
.sr-bar-row { display:flex; align-items:center; gap:10px; }
.sr-bar-label { width:76px; font-size:13px; color:#666; flex-shrink:0; }
.sr-bar-track { flex:1; height:8px; border-radius:4px; background:#f0f3f7; overflow:hidden; }
.sr-bar-fill { height:100%; border-radius:4px; background:linear-gradient(90deg,#ffb020,#ff8a2b); }
.sr-bar-num { width:32px; text-align:right; font-size:13px; color:#7b8797; }

.sr-extra { display:flex; justify-content:space-between; margin-top:16px; padding-top:14px; border-top:1px solid #f2f4f7; font-size:13px; color:#7b8797; }
.sr-extra b { color:var(--brand); font-size:15px; }

.sr-list { padding:12px 20px 0; }
.sr-item { background:#fff; border-radius:16px; padding:16px; margin-bottom:12px; box-shadow:0 4px 12px rgba(0,0,0,.04); }
.sr-item-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }
.sr-user { font-size:15px; font-weight:700; color:#333; }
.sr-stars { color:#ffb020; font-size:13px; }
.sr-content { font-size:15px; color:#4a5565; line-height:1.7; }
.sr-imgs { display:flex; gap:8px; margin-top:10px; }
.sr-img { width:74px; height:74px; border-radius:10px; object-fit:cover; background:#eef2f7; }
.sr-date { display:block; margin-top:10px; font-size:12px; color:#9aa6b5; }

.sr-tip { text-align:center; font-size:14px; color:#9aa6b5; padding:22px 0; }
</style>
