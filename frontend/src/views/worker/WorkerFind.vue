<!-- frontend/src/views/worker/WorkerFind.vue —— 大字版「找活」大厅
     设计来源：参考图（找活 tab）
       滚动前：搜索框 + 八宫格图标
       滚动后：八宫格收起 → 一行可横滑的文字标签吸顶
     卡片：标题 + 薪资 / 年龄或地区 | 企业 / 标签
-->
<template>
  <div class="wf-page">
    <!-- 顶部：搜索 + 折叠后的文字标签 -->
    <header class="wf-top">
      <div class="wf-search">
        <span class="wf-search-ico">🔍</span>
        <input
          v-model="keyword"
          class="wf-search-input"
          placeholder="搜索：普工、叉车、保洁"
          @keyup.enter="handleSearch"
        />
        <button v-if="keyword" class="wf-clear" @click="clearKeyword">✕</button>
      </div>

      <div v-show="collapsed" class="wf-strip">
        <button
          v-for="c in cats"
          :key="c.label"
          :class="['wf-strip-item', { on: activeCat === c.label }]"
          @click="pickCat(c)"
        >
          {{ c.label }}
        </button>
      </div>
    </header>

    <!-- 八宫格（未折叠时） -->
    <section v-show="!collapsed" class="wf-cats">
      <button
        v-for="c in cats"
        :key="c.label"
        :class="['wf-cat', { hot: c.hot, on: activeCat === c.label }]"
        @click="pickCat(c)"
      >
        <span class="wf-cat-ico">{{ c.icon }}</span>
        <span class="wf-cat-label">{{ c.label }}</span>
      </button>
    </section>

    <!-- 岗位列表 -->
    <section class="wf-list">
      <article v-for="job in jobs" :key="job.id" class="wf-card" @click="goDetail(job.id)">
        <div class="wf-row1">
          <h3 class="wf-title">{{ job.title }}</h3>
          <span class="wf-price">{{ job.salary }}</span>
        </div>
        <p class="wf-row2">
          <span class="wf-hl">{{ job.location }}</span>
          <template v-if="job.company_name"> | {{ job.company_name }}</template>
        </p>
        <div class="wf-tags">
          <span class="wf-tag">{{ job.filter_tag || '日结' }}</span>
          <span class="wf-tag gray">{{ job.job_type === 'long_term' ? '长期' : '短期' }}</span>
        </div>
      </article>

      <p v-if="loading" class="wf-tip">加载中…</p>
      <p v-else-if="!jobs.length" class="wf-tip">暂无岗位，换个关键词或分类试试</p>
      <p v-else-if="noMore" class="wf-tip">— 已经到底了 —</p>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()

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
const activeCat = ref('')
const keyword = ref('')

const jobs = ref([])
const page = ref(1)
const size = 10
const loading = ref(false)
const noMore = ref(false)

// 滚动折叠
const collapsed = ref(false)
const COLLAPSE_AT = 88

function onScroll() {
  collapsed.value = window.scrollY > COLLAPSE_AT
}

async function loadJobs(append = false) {
  if (loading.value) return
  loading.value = true
  try {
    const res = await api.get('/jobs/list', {
      params: { keyword: keyword.value, page: page.value, size }
    })
    const rows = res.data || []
    jobs.value = append ? [...jobs.value, ...rows] : rows
    noMore.value = jobs.value.length >= (res.total || 0)
  } catch (err) {
    if (!append) jobs.value = []
    if (window.$toast) window.$toast(err.response?.data?.detail || '岗位加载失败')
    noMore.value = true
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  noMore.value = false
  loadJobs(false)
}

function pickCat(cat) {
  activeCat.value = activeCat.value === cat.label ? '' : cat.label
  keyword.value = activeCat.value
  handleSearch()
  // 收起状态下切换分类，滚动回顶部更符合预期
  if (collapsed.value) window.scrollTo({ top: 0, behavior: 'smooth' })
}

function clearKeyword() {
  keyword.value = ''
  activeCat.value = ''
  handleSearch()
}

function goDetail(id) {
  router.push(`/worker/job-detail/${id}`)
}

// 滚动到底自动加载下一页
function maybeLoadMore() {
  const nearBottom = window.innerHeight + window.scrollY >= document.body.scrollHeight - 200
  if (nearBottom && !loading.value && !noMore.value) {
    page.value += 1
    loadJobs(true)
  }
}

function onWindowScroll() {
  onScroll()
  maybeLoadMore()
}

onMounted(() => {
  loadJobs(false)
  window.addEventListener('scroll', onWindowScroll, { passive: true })
  onScroll()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onWindowScroll)
})
</script>

<style scoped>
.wf-page {
  min-height: 100vh;
  background: var(--bg, #eef1f5);
  padding-bottom: 20px;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.wf-top {
  position: sticky;
  top: 0;
  z-index: 20;
  background: #fff;
  padding: 12px 20px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}
.wf-search {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 46px;
  padding: 0 16px;
  background: var(--bg);
  border-radius: 999px;
}
.wf-search-ico { font-size: 15px; }
.wf-search-input {
  flex: 1;
  border: none;
  background: none;
  outline: none;
  font-size: 16px;
  color: #111;
  min-width: 0;
}
.wf-search-input::placeholder { color: #9aa6b5; }
.wf-clear {
  border: none;
  background: #dfe5ee;
  color: #fff;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  font-size: 12px;
}

/* 折叠后的文字标签条 */
.wf-strip {
  display: flex;
  gap: 20px;
  padding: 12px 0 10px;
  overflow-x: auto;
  white-space: nowrap;
  border-top: 1px solid #f2f4f7;
  margin-top: 10px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.wf-strip::-webkit-scrollbar { display: none; }
.wf-strip-item {
  flex-shrink: 0;
  border: none;
  background: none;
  padding: 0;
  font-size: 15px;
  font-weight: 700;
  color: #333;
}
.wf-strip-item.on { color: var(--price, #ff7a1a); }

/* 八宫格 */
.wf-cats {
  display: flex;
  flex-wrap: wrap;
  background: #fff;
  padding: 16px 10px 18px;
  margin-bottom: 12px;
}
.wf-cat {
  width: 25%;
  border: none;
  background: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
}
.wf-cat-ico {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: #f9fafc;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 23px;
}
.wf-cat-label { font-size: 14px; font-weight: 700; color: #333; }
.wf-cat.hot .wf-cat-ico { background: var(--price-soft, #fff1e6); border: 1px solid var(--price, #ff7a1a); }
.wf-cat.hot .wf-cat-label { color: var(--price, #ff7a1a); }
.wf-cat.on .wf-cat-ico { background: var(--price, #ff7a1a); border-color: var(--price, #ff7a1a); }
.wf-cat.on .wf-cat-label { color: var(--price, #ff7a1a); }

/* 岗位卡片（纯文字版） */
.wf-list { padding: 0 20px; }
.wf-card {
  background: #fff;
  border-radius: 16px;
  padding: 18px 20px;
  margin-bottom: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}
.wf-row1 {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}
.wf-title {
  font-size: 20px;
  font-weight: 800;
  color: #111;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.wf-price {
  font-size: 20px;
  font-weight: 800;
  color: var(--price, #ff7a1a);
  flex-shrink: 0;
}
.wf-row2 {
  margin: 8px 0 12px;
  font-size: 15px;
  font-weight: 600;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.wf-hl { color: var(--price, #ff7a1a); font-weight: 800; margin-right: 6px; }
.wf-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.wf-tag {
  background: var(--price-soft, #fff1e6);
  color: var(--price, #ff7a1a);
  font-size: 13px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 6px;
}
.wf-tag.gray { background: var(--bg); color: #555; }

.wf-tip { text-align: center; font-size: 14px; color: #9aa6b5; padding: 22px 0; }
</style>
