<!-- frontend/src/views/worker/JobDetail.vue —— 大字版岗位详情
     设计来源：0暂放资料/UI橙色大字  C端求职.html P7
     规则：未登录可浏览；点击「立即报名」才跳登录，登录后回到本页
-->
<template>
  <div class="jd-page">
    <!-- 顶部导航 -->
    <header class="jd-nav">
      <button class="jd-back" @click="$router.back()">‹</button>
      <span class="jd-nav-title">岗位详情</span>
      <span class="jd-nav-right"></span>
    </header>

    <div v-if="loading" class="jd-tip">加载中…</div>

    <template v-else-if="job">
      <!-- 封面 -->
      <div class="jd-cover">
        <img v-if="coverUrl && !coverFailed" :src="coverUrl" class="jd-cover-img" alt="" @error="coverFailed = true" />
        <span v-else class="jd-cover-fallback">{{ (job.title || '岗')[0] }}</span>
        <span class="jd-cover-tag">{{ job.filter_tag || '日结' }}</span>
      </div>

      <!-- 核心信息 -->
      <section class="jd-card">
        <div class="jd-head">
          <h1 class="jd-title">{{ job.title }}</h1>
          <span class="jd-price">{{ job.salary }}</span>
        </div>
        <p class="jd-meta">◎ {{ job.location }}<template v-if="job.district"> · {{ job.district }}</template></p>
        <div class="jd-tags">
          <span class="jd-tag">{{ job.filter_tag || '日结' }}</span>
          <span class="jd-tag gray">{{ job.job_type === 'long_term' ? '长期工' : '短期工' }}</span>
          <span v-if="job.created_at" class="jd-tag gray">发布于 {{ job.created_at }}</span>
        </div>
      </section>

      <!-- 我的应聘进度（通用组件：覆盖投递→初筛→面试→录用→完工，含异常分支） -->
      <section v-if="myApp" class="jd-card">
        <h2 class="jd-h2">我的应聘进度</h2>
        <OrderTimeline :app="myApp" />
      </section>

      <!-- 岗位要求 -->
      <section class="jd-card">
        <h2 class="jd-h2">岗位要求</h2>
        <p class="jd-text">{{ job.requirement || '暂无特殊要求，可直接报名' }}</p>
      </section>

      <!-- 岗位描述 -->
      <section class="jd-card">
        <h2 class="jd-h2">工作内容</h2>
        <p class="jd-text">{{ job.description || '暂无描述' }}</p>
      </section>

      <!-- 企业信息 -->
      <section class="jd-card">
        <h2 class="jd-h2">企业信息</h2>
        <div class="jd-company">
          <div class="jd-company-logo">{{ (company.company_name || '企')[0] }}</div>
          <div class="jd-company-body">
            <div class="jd-company-name">{{ company.company_name || '未知企业' }}</div>
            <div class="jd-company-sub">
              {{ company.industry || '企业' }}<template v-if="company.district"> · {{ company.district }}</template>
            </div>
          </div>
          <span class="jd-verified">已认证</span>
        </div>
        <p class="jd-text mt10">{{ company.intro || '暂无简介' }}</p>
      </section>

      <!-- 平台提示 -->
      <section class="jd-card warn">
        <h2 class="jd-h2">平台温馨提示</h2>
        <p class="jd-text">
          本岗位由平台审核后发布。任何以「押金、服装费、培训费」等名义收费的，均为违规，
          请立即举报；平台不参与线下交易，请注意人身与财产安全。
        </p>
      </section>

      <div class="jd-bottom-space"></div>

      <!-- 底部操作栏 -->
      <div class="jd-action">
        <button class="jd-btn ghost" :class="{ active: favorited }" @click="collect">
          {{ favorited ? '已收藏' : '收藏' }}
        </button>
        <button class="jd-btn primary" :disabled="applied || submitting" @click="apply">
          {{ applied ? '已报名' : (submitting ? '提交中…' : '立即报名') }}
        </button>
      </div>
    </template>

    <div v-else class="jd-tip">岗位不存在或已下架</div>

    <!-- 投递确认弹窗（P7b） -->
    <div v-if="confirmOpen" class="jd-mask" @click.self="confirmOpen = false">
      <div class="jd-sheet">
        <div class="jd-sheet-head">
          <h3>确认报名</h3>
          <span class="jd-sheet-close" @click="confirmOpen = false">✕</span>
        </div>

        <div class="jd-sheet-job">
          <div class="jd-sheet-info">
            <div class="jd-sheet-title">{{ job && job.title }}</div>
            <div class="jd-sheet-meta">{{ company.company_name }} · {{ job && job.location }}</div>
          </div>
          <span class="jd-sheet-price">{{ job && job.salary }}</span>
        </div>

        <p v-if="!verified" class="jd-sheet-warn">
          你尚未完成实名认证，报名前需先完成「实名信息 + 人脸核验」。
        </p>

        <ul class="jd-sheet-tips">
          <li>报名后企业可查看你的简历与联系方式</li>
          <li>同一岗位不可重复报名</li>
          <li>平台不收取任何费用，遇收费请立即举报</li>
        </ul>

        <div class="jd-sheet-actions">
          <button class="jd-btn ghost" @click="confirmOpen = false">再想想</button>
          <button class="jd-btn primary" :disabled="submitting" @click="confirmApply">
            {{ submitting ? '提交中…' : '确认报名' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api'
import OrderTimeline from '../../components/OrderTimeline.vue'
import { isFavorite, toggleFavorite } from '../../utils/favorites'

const route = useRoute()
const router = useRouter()

const job = ref(null)
const company = ref({})
const loading = ref(true)
const submitting = ref(false)
const applied = ref(false)
const coverFailed = ref(false)
const confirmOpen = ref(false)
const verified = ref(true)
const myApp = ref(null)
const favorited = ref(false)

const coverUrl = computed(() => {
  if (!job.value) return ''
  if (job.value.cover_image) return job.value.cover_image
  return `https://picsum.photos/seed/linggong${job.value.id}/720/420`
})

const isLogged = () => !!localStorage.getItem('token')

// 推广归属：从推广链接 ?promoter= 带入，投递时落库
const promoter = Number(route.query.promoter) || null

async function loadDetail() {
  loading.value = true
  try {
    const res = await api.get(`/jobs/${route.params.id}`)
    job.value = res.data.job
    company.value = res.data.company || {}
    favorited.value = isFavorite(job.value.id)
    await checkApplied()
  } catch (err) {
    job.value = null
    if (window.$toast) window.$toast(err.response?.data?.detail || '岗位加载失败')
  } finally {
    loading.value = false
  }
}

async function checkApplied() {
  if (!isLogged() || !job.value) return
  try {
    const res = await api.get('/jobs/my-applications')
    const rows = Array.isArray(res.data) ? res.data : []
    const row = rows.find((r) => String(r.job_id) === String(job.value.id))
    applied.value = !!row
    // 用于「我的应聘进度」进度条
    myApp.value = row || null
  } catch (err) {
    // 游客或被拦截时忽略
  }

  try {
    const p = await api.get('/user/profile')
    verified.value = p.data?.verify_status === 'verified'
  } catch (err) {
    verified.value = false
  }
}

function needLoginThenReturn() {
  const target = route.fullPath
  window.$toast && window.$toast('登录后即可报名')
  // 意图驱动：投递动作 → 直接进求职者登录，无需选角色
  router.push({ path: '/login', query: { role: 'worker', redirect: target } })
}

function apply() {
  if (applied.value) return

  // 🚨 游客拦截：先浏览后登录，登录成功回跳本页
  if (!isLogged()) return needLoginThenReturn()

  // 打开确认弹窗（P7b）
  confirmOpen.value = true
}

async function confirmApply() {
  submitting.value = true
  try {
    await api.post(`/jobs/apply/${job.value.id}`, { resume_id: '' },
      promoter ? { params: { promoter } } : undefined)
    applied.value = true
    confirmOpen.value = false
    window.$toast && window.$toast('报名成功，请在「我的投递」查看进度')
  } catch (err) {
    const status = err.response?.status
    if (status === 401) {
      confirmOpen.value = false
      return needLoginThenReturn()
    }
    const detail = err.response?.data?.detail || '报名失败'
    window.$toast && window.$toast(detail)
    // 未实名 → 引导去认证
    if (status === 403 && String(detail).includes('实名')) {
      confirmOpen.value = false
      router.push('/worker/verify')
    }
  } finally {
    submitting.value = false
  }
}

function collect() {
  if (!job.value) return
  const nowFav = toggleFavorite(job.value.id)
  favorited.value = nowFav
  window.$toast && window.$toast(nowFav ? '已加入收藏' : '已取消收藏')
}

onMounted(loadDetail)
</script>

<style scoped>
.jd-page {
  --dz-brand: var(--brand, #1677ff);
  --dz-brand-soft: var(--brand-soft, #eaf2ff);
  --dz-bg: var(--bg, #eef1f5);
  --dz-text: var(--text, #1d2531);
  min-height: 100vh;
  background: var(--dz-bg);
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.jd-nav {
  position: sticky;
  top: 0;
  z-index: 20;
  height: 56px;
  background: #fff;
  display: flex;
  align-items: center;
  padding: 0 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}
.jd-back {
  border: none;
  background: none;
  font-size: 30px;
  line-height: 1;
  color: #333;
  width: 40px;
  text-align: left;
  padding-bottom: 6px;
}
.jd-nav-title { flex: 1; text-align: center; font-size: 18px; font-weight: 700; color: var(--dz-text); }
.jd-nav-right { width: 40px; }

.jd-cover {
  position: relative;
  height: 200px;
  background: linear-gradient(135deg, #ffe3cc, #ffd0b0);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.jd-cover-img { width: 100%; height: 100%; object-fit: cover; }
.jd-cover-fallback { font-size: 64px; font-weight: 800; color: #fff; text-shadow: 0 4px 12px rgba(0,0,0,.18); }
.jd-cover-tag {
  position: absolute;
  left: 20px;
  bottom: 14px;
  background: var(--dz-brand);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 8px;
}

.jd-card {
  background: #fff;
  border-radius: 16px;
  padding: 18px 20px;
  margin: 12px 20px 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}
.jd-card.warn { background: #fffaf3; border: 1px solid #ffe3cc; }

.jd-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}
.jd-title { font-size: 24px; font-weight: 800; color: var(--dz-text); line-height: 1.25; }
.jd-price { font-size: 22px; font-weight: 800; color: var(--dz-brand); flex-shrink: 0; }
.jd-meta { font-size: 15px; color: #7b8797; margin-bottom: 12px; }

.jd-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.jd-tag {
  background: var(--dz-brand-soft);
  color: var(--dz-brand);
  font-size: 13px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 6px;
}
.jd-tag.gray { background: var(--dz-bg); color: #555; }

.jd-h2 { font-size: 18px; font-weight: 800; color: var(--dz-text); margin-bottom: 10px; }
.jd-text { font-size: 15px; color: #4a5565; line-height: 1.7; white-space: pre-wrap; }
.jd-text.mt10 { margin-top: 10px; }

.jd-company { display: flex; align-items: center; gap: 12px; }
.jd-company-logo {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--dz-brand-soft);
  color: var(--dz-brand);
  font-size: 20px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.jd-company-body { flex: 1; min-width: 0; }
.jd-company-name { font-size: 17px; font-weight: 700; color: var(--dz-text); }
.jd-company-sub { font-size: 13px; color: #7b8797; margin-top: 3px; }
.jd-verified {
  font-size: 12px;
  color: #0f9d58;
  border: 1px solid #b7e3c8;
  background: #f2fbf5;
  padding: 3px 8px;
  border-radius: 6px;
  flex-shrink: 0;
}

.jd-bottom-space { height: 130px; }

.jd-action {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 60px;
  display: flex;
  gap: 12px;
  padding: 10px 20px 12px;
  background: #fff;
  border-top: 1px solid #eef0f3;
  z-index: 15;
}
.jd-btn {
  border: none;
  height: 50px;
  border-radius: 12px;
  font-size: 17px;
  font-weight: 800;
}
.jd-btn.ghost {
  width: 104px;
  background: var(--dz-bg);
  color: #555;
}
.jd-btn.primary {
  flex: 1;
  background: var(--dz-brand);
  color: #fff;
}
.jd-btn.ghost.active { color: var(--dz-brand); font-weight: 800; }
.jd-btn.primary:disabled { opacity: 0.6; }

.jd-tip { text-align: center; color: #9aa6b5; font-size: 15px; padding: 60px 0; }

/* 投递确认弹窗 */
.jd-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.42);
  z-index: 200;
  display: flex;
  align-items: flex-end;
}
.jd-sheet {
  width: 100%;
  background: #fff;
  border-radius: 20px 20px 0 0;
  padding: 20px 20px 26px;
}
.jd-sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.jd-sheet-head h3 { font-size: 20px; font-weight: 800; color: var(--dz-text); }
.jd-sheet-close { font-size: 18px; color: #9aa6b5; padding: 4px; }

.jd-sheet-job {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: var(--dz-bg);
  border-radius: 14px;
  padding: 14px 16px;
}
.jd-sheet-info { min-width: 0; }
.jd-sheet-title {
  font-size: 18px;
  font-weight: 800;
  color: var(--dz-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.jd-sheet-meta { font-size: 13px; color: #7b8797; margin-top: 4px; }
.jd-sheet-price { font-size: 19px; font-weight: 800; color: var(--dz-brand); flex-shrink: 0; }

.jd-sheet-warn {
  margin-top: 14px;
  background: var(--dz-brand-soft);
  color: var(--dz-brand);
  font-size: 14px;
  font-weight: 600;
  line-height: 1.6;
  padding: 12px 14px;
  border-radius: 12px;
}

.jd-sheet-tips {
  margin: 14px 0 20px;
  padding-left: 18px;
  color: #7b8797;
  font-size: 13px;
  line-height: 1.9;
}

.jd-sheet-actions { display: flex; gap: 12px; }
.jd-sheet-actions .jd-btn.ghost { width: 34%; }
.jd-sheet-actions .jd-btn.primary { flex: 1; }
</style>
