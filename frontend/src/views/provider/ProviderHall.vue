<!-- frontend/src/views/provider/ProviderHall.vue —— 服务商端「招聘大厅」
     搜索 + 八宫格 + 岗位卡片（分享 / 立即报名）
-->
<template>
  <div class="ph-page">
    <header class="ph-top">
      <div class="ph-search">
        <span>🔍</span>
        <input v-model="keyword" placeholder="搜索：普工、叉车、保洁" @keyup.enter="load" />
        <button v-if="keyword" class="ph-clear" @click="clearKeyword">✕</button>
      </div>

      <div class="ph-cats">
        <button
          v-for="c in cats"
          :key="c.label"
          :class="['ph-cat', { hot: c.hot, on: activeCat === c.label }]"
          @click="pickCat(c)"
        >
          <span class="ph-cat-ico">{{ c.icon }}</span>
          <span class="ph-cat-label">{{ c.label }}</span>
        </button>
      </div>
    </header>

    <section class="ph-list">
      <article v-for="job in list" :key="job.id" class="ph-card">
        <div class="ph-row1">
          <h3 class="ph-title">{{ job.title }}</h3>
          <span class="ph-price">{{ job.salary }}</span>
        </div>
        <p class="ph-row2">
          <span class="ph-hl">{{ job.location }}</span>
          <template v-if="job.company_name"> | {{ job.company_name }}</template>
        </p>
        <div class="ph-row3">
          <div class="ph-tags">
            <span class="ph-tag">{{ job.filter_tag || '日结' }}</span>
            <span class="ph-tag gray">{{ job.job_type === 'long_term' ? '长期' : '短期' }}</span>
          </div>
          <div class="ph-ops">
            <button class="ph-op" @click.stop="copyLink(job)">复制链接</button>
            <button class="ph-op primary" @click.stop="promote(job)">立即推广</button>
          </div>
        </div>
      </article>

      <p v-if="loading" class="ph-tip">加载中…</p>
      <p v-else-if="!list.length" class="ph-tip">暂无岗位</p>
      <p v-else class="ph-tip">— 已经到底了 —</p>
    </section>

    <!-- 推广弹窗 -->
    <div v-if="promoteOpen" class="ph-mask" @click.self="promoteOpen = false">
      <div class="ph-sheet">
        <div class="ph-sheet-head">
          <h3>推广岗位</h3>
          <span class="ph-sheet-close" @click="promoteOpen = false">✕</span>
        </div>

        <div class="ph-sheet-job">
          <div class="ph-sheet-info">
            <div class="ph-sheet-title">{{ promoteJob && promoteJob.title }}</div>
            <div class="ph-sheet-meta">{{ promoteJob && promoteJob.company_name }} · {{ promoteJob && promoteJob.location }}</div>
          </div>
          <span class="ph-sheet-price">{{ promoteJob && promoteJob.salary }}</span>
        </div>

        <p class="ph-sheet-label">你的专属推广链接</p>
        <div class="ph-link-box">{{ promoteLink }}</div>

        <p class="ph-sheet-note">
          把链接分享给工友，对方投递后系统会记录你是推广人；成功入职可结算推广激励。
          <span v-if="promoterCount">当前已有 {{ promoterCount }} 位推广人。</span>
        </p>

        <div class="ph-sheet-actions">
          <button class="ph-op" @click="promoteOpen = false">关闭</button>
          <button class="ph-op primary" @click="doCopy">复制链接</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const cats = [
  { icon: '💼', label: '正式工岗' },
  { icon: '🏭', label: '厂区直招' },
  { icon: '💵', label: '日结周结', hot: true },
  { icon: '🛵', label: '外卖快递' },
  { icon: '🛠️', label: '技术工种' },
  { icon: '👴', label: '大龄兜底' },
  { icon: '🍱', label: '餐饮兼职' },
  { icon: '📦', label: '分拣搬运' }
]

const keyword = ref('')
const activeCat = ref('')
const list = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await api.get('/jobs/list', { params: { keyword: keyword.value, page: 1, size: 20 } })
    list.value = res.data || []
  } catch (err) {
    list.value = []
    if (window.$toast) window.$toast(err.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

function pickCat(c) {
  activeCat.value = activeCat.value === c.label ? '' : c.label
  keyword.value = activeCat.value
  load()
}
function clearKeyword() {
  keyword.value = ''
  activeCat.value = ''
  load()
}

function share(job) {
  const link = `${window.location.origin}${window.location.pathname}#/worker/job-detail/${job.id}`
  navigator.clipboard?.writeText(link).then(
    () => window.$toast && window.$toast('岗位链接已复制'),
    () => window.$toast && window.$toast('复制失败，请手动分享')
  )
}

// 推广状态
const promoteOpen = ref(false)
const promoteJob = ref(null)
const promoteLink = ref('')
const promoterCount = ref(0)

function buildLink(job) {
  return `${window.location.origin}${window.location.pathname}#/worker/job-detail/${job.id}`
}

function copyLink(job) {
  const link = buildLink(job)
  navigator.clipboard?.writeText(link).then(
    () => window.$toast && window.$toast('岗位链接已复制'),
    () => window.$toast && window.$toast('复制失败，请手动分享')
  )
}

async function promote(job) {
  promoteJob.value = job
  promoteLink.value = buildLink(job)
  promoterCount.value = 0
  promoteOpen.value = true

  try {
    const res = await api.post(`/jobs/${job.id}/promote`)
    const data = res.data || {}
    if (data.link) {
      promoteLink.value = `${window.location.origin}${window.location.pathname}#${data.link.split('#')[1] || data.link}`
    }
    promoterCount.value = data.promoters || 0
  } catch (err) {
    window.$toast && window.$toast(err.response?.data?.detail || '推广记录失败，链接仍可复制')
  }
}

function doCopy() {
  navigator.clipboard?.writeText(promoteLink.value).then(
    () => window.$toast && window.$toast('推广链接已复制，快分享给工友吧'),
    () => window.$toast && window.$toast('复制失败，请长按手动复制')
  )
}

onMounted(load)
</script>

<style scoped>
.ph-page { min-height: 100vh; background: var(--bg); padding-bottom: 12px; }

.ph-top {
  position: sticky;
  top: 0;
  z-index: 20;
  background: #fff;
  padding: 12px 20px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}
.ph-search {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 44px;
  padding: 0 16px;
  background: var(--bg);
  border-radius: 999px;
}
.ph-search input { flex: 1; border: none; background: none; outline: none; font-size: 15px; min-width: 0; }
.ph-clear { border: none; background: #dfe5ee; color: #fff; width: 20px; height: 20px; border-radius: 50%; font-size: 12px; }

.ph-cats { display: flex; flex-wrap: wrap; padding: 14px 0 16px; }
.ph-cat { width: 25%; border: none; background: none; display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 4px 0; }
.ph-cat-ico { width: 46px; height: 46px; border-radius: 14px; background: #f9fafc; display: flex; align-items: center; justify-content: center; font-size: 23px; }
.ph-cat-label { font-size: 13px; font-weight: 700; color: #333; }
.ph-cat.hot .ph-cat-ico { background: #fff1e6; border: 1px solid #ff6b00; }
.ph-cat.hot .ph-cat-label { color: #ff6b00; }
.ph-cat.on .ph-cat-ico { background: var(--g-soft); border: 1px solid var(--g); }
.ph-cat.on .ph-cat-label { color: var(--g-text); }

.ph-list { padding: 12px 20px 0; }
.ph-card {
  background: #fff;
  border-radius: 16px;
  padding: 18px 20px;
  margin-bottom: 12px;
  border: 1px solid var(--line);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}
.ph-row1 { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; }
.ph-title { font-size: 20px; font-weight: 800; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ph-price { font-size: 20px; font-weight: 800; color: #ff6b00; flex-shrink: 0; }
.ph-row2 { margin: 8px 0 14px; font-size: 14px; font-weight: 600; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ph-hl { color: #ff6b00; font-weight: 800; margin-right: 6px; }

.ph-row3 { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.ph-tags { display: flex; gap: 8px; }
.ph-tag { background: #fff1e6; color: #ff6b00; font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 6px; }
.ph-tag.gray { background: var(--bg); color: #555; }
.ph-ops { display: flex; gap: 8px; flex-shrink: 0; }
.ph-op {
  height: 32px;
  padding: 0 14px;
  border-radius: 999px;
  border: none;
  background: var(--bg);
  color: #555;
  font-size: 13px;
  font-weight: 700;
}
.ph-op.primary { background: #ff6b00; color: #fff; }

.ph-tip { text-align: center; font-size: 14px; color: #9aa6b5; padding: 22px 0; }

/* 推广弹窗 */
.ph-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.42);
  z-index: 200;
  display: flex;
  align-items: flex-end;
}
.ph-sheet {
  width: 100%;
  background: #fff;
  border-radius: 20px 20px 0 0;
  padding: 20px 20px 26px;
}
.ph-sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.ph-sheet-head h3 { font-size: 20px; font-weight: 800; color: var(--text); }
.ph-sheet-close { font-size: 18px; color: #9aa6b5; padding: 4px; }

.ph-sheet-job {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: var(--bg);
  border-radius: 14px;
  padding: 14px 16px;
}
.ph-sheet-info { min-width: 0; }
.ph-sheet-title { font-size: 18px; font-weight: 800; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ph-sheet-meta { font-size: 13px; color: #7b8797; margin-top: 4px; }
.ph-sheet-price { font-size: 19px; font-weight: 800; color: #ff6b00; flex-shrink: 0; }

.ph-sheet-label { margin: 18px 0 8px; font-size: 14px; font-weight: 700; color: #333; }
.ph-link-box {
  background: var(--bg);
  border: 1px dashed var(--g);
  border-radius: 12px;
  padding: 14px;
  font-size: 13px;
  color: var(--g-text);
  word-break: break-all;
  line-height: 1.6;
}
.ph-sheet-note {
  margin: 14px 0 20px;
  font-size: 13px;
  color: #7b8797;
  line-height: 1.7;
}
.ph-sheet-actions { display: flex; gap: 12px; }
.ph-sheet-actions .ph-op { height: 50px; flex: 1; font-size: 16px; }
.ph-sheet-actions .ph-op.primary { flex: 2; }
</style>
