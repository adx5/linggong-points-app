<!-- frontend/src/views/worker/WorkerHome.vue —— 大字版 C 端首页（门面）
     布局参考：0暂放资料/UI 蓝色  C端求职首页.html
     结构：横幅口号 + 城市切换 + 搜索 → 排序胶囊 → 精选岗位图文 → 岗位列表
     配色沿用大字版橙（与找活/同城保持一致）
-->
<template>
  <div class="dz-home">
    <!-- 顶部横幅 -->
    <header class="dz-hero">
      <div class="dz-deco dz-deco-1"></div>
      <div class="dz-deco dz-deco-2"></div>

      <button class="dz-city" @click="openCitySheet">
        <span class="dz-pin">◎</span>
        <span class="dz-city-name">{{ cityName }}</span>
        <span class="dz-caret">▾</span>
      </button>

      <div class="dz-slogan">
        <h1>零工小市场</h1>
        <h2>就业大民生</h2>
      </div>

      <div class="dz-search-row">
        <div class="dz-search">
          <span class="dz-search-ico">🔍</span>
          <input
            v-model="keyword"
            class="dz-search-input"
            placeholder="搜索岗位、公司、地点"
            @keyup.enter="reload"
          />
        </div>
        <button class="dz-search-btn" @click="reload">搜索</button>
      </div>
    </header>

    <!-- 排序胶囊 -->
    <nav class="dz-tabs">
      <button
        v-for="t in tabs"
        :key="t.key"
        :class="['dz-tab', { active: activeTab === t.key }]"
        @click="switchTab(t.key)"
      >
        {{ t.label }}
      </button>
      <span v-if="activeDistrict" class="dz-district-chip" @click="clearDistrict">
        {{ activeDistrict }} ✕
      </span>
    </nav>

    <!-- 精选岗位 -->
    <section v-if="featured" class="dz-block">
      <div class="dz-block-head">
        <h2>精选岗位</h2>
        <span class="dz-more" @click="goFind">更多 ›</span>
      </div>
      <article class="dz-feature" @click="goDetail(featured.id)">
        <div class="dz-feature-cover">
          <img
            v-if="!coverFailed[featured.id] && coverOf(featured)"
            :src="coverOf(featured)"
            class="dz-cover-img"
            alt=""
            @error="markCoverFailed(featured.id)"
          />
          <span v-else class="dz-cover-fallback">{{ (featured.title || '岗')[0] }}</span>
          <span class="dz-feature-badge">今日推荐</span>
        </div>
        <div class="dz-feature-body">
          <div class="dz-feature-head">
            <h3 class="dz-feature-title">{{ featured.title }}</h3>
            <span class="dz-price">{{ featured.salary }}</span>
          </div>
          <p class="dz-meta">◎ {{ featured.location }}<template v-if="featured.company_name"> · {{ featured.company_name }}</template></p>
          <div class="dz-tags">
            <span class="dz-tag">{{ featured.filter_tag || '日结' }}</span>
            <span class="dz-tag gray">{{ featured.job_type === 'long_term' ? '长期' : '短期' }}</span>
          </div>
        </div>
      </article>
    </section>

    <!-- 岗位列表 -->
    <section class="dz-list">
      <article v-for="job in list" :key="job.id" class="dz-card" @click="goDetail(job.id)">
        <div class="dz-card-cover">
          <img
            v-if="!coverFailed[job.id] && coverOf(job)"
            :src="coverOf(job)"
            class="dz-cover-img"
            alt=""
            @error="markCoverFailed(job.id)"
          />
          <span v-else class="dz-cover-fallback">{{ (job.title || '岗')[0] }}</span>
        </div>
        <div class="dz-card-body">
          <div class="dz-card-head">
            <h3 class="dz-card-title">{{ job.title }}</h3>
            <span class="dz-price sm">{{ job.salary }}</span>
          </div>
          <p class="dz-meta">◎ {{ job.location }}<template v-if="job.company_name"> · {{ job.company_name }}</template></p>
          <div class="dz-tags">
            <span class="dz-tag">{{ job.filter_tag || '日结' }}</span>
            <span class="dz-tag gray">{{ job.job_type === 'long_term' ? '长期' : '短期' }}</span>
          </div>
          <div class="dz-card-foot">
            <span v-if="job.description" class="dz-desc">{{ job.description }}</span>
            <button class="dz-look">查看 ›</button>
          </div>
        </div>
      </article>

      <p v-if="loading" class="dz-tip">正在加载…</p>
      <p v-else-if="!list.length" class="dz-tip">当前城市暂无岗位，换个城市或关键词试试</p>
      <p v-else class="dz-tip">— 已经到底了 —</p>
    </section>

    <!-- 城市弹层 -->
    <div v-if="sheetOpen" class="dz-mask" @click.self="sheetOpen = false">
      <div class="dz-sheet">
        <div class="dz-sheet-head">
          <h3>选择城市</h3>
          <span class="dz-sheet-close" @click="sheetOpen = false">✕</span>
        </div>
        <p class="dz-sheet-sub">切换后仅展示该城市的岗位</p>
        <div class="dz-city-list">
          <button
            v-for="c in cities"
            :key="c.id"
            :class="['dz-city-item', { active: c.id === cityId }]"
            @click="chooseCity(c)"
          >
            <span>{{ c.name }}</span>
            <span v-if="c.id === cityId">✓</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 区域弹层（附近） -->
    <div v-if="districtOpen" class="dz-mask" @click.self="districtOpen = false">
      <div class="dz-sheet">
        <div class="dz-sheet-head">
          <h3>选择区域</h3>
          <span class="dz-sheet-close" @click="districtOpen = false">✕</span>
        </div>
        <p class="dz-sheet-sub">按企业所在区/镇筛选附近岗位</p>
        <div class="dz-city-list">
          <button
            v-for="d in districts"
            :key="d"
            :class="['dz-city-item', { active: d === activeDistrict }]"
            @click="chooseDistrict(d)"
          >
            <span>{{ d }}</span>
            <span v-if="d === activeDistrict">✓</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()

const keyword = ref('')
const loading = ref(false)
const list = ref([])
const featured = ref(null)

const tabs = [
  { key: 'recommend', label: '推荐' },
  { key: 'newest', label: '最新' },
  { key: 'salary', label: '高薪' },
  { key: 'nearby', label: '附近' }
]
const activeTab = ref('recommend')

// 城市
const cities = ref([])
const cityId = ref(localStorage.getItem('guest_city_id') || '410185')
const cityName = ref('登封')
const sheetOpen = ref(false)

// 附近（区镇）
const districts = ref([])
const activeDistrict = ref(localStorage.getItem('guest_district') || '')
const districtOpen = ref(false)

const coverFailed = ref({})

function coverOf(job) {
  if (job.cover_image) return job.cover_image
  return `https://picsum.photos/seed/linggong${job.id}/240/240`
}
function markCoverFailed(id) {
  coverFailed.value = { ...coverFailed.value, [id]: true }
}

function salaryValue(text) {
  const m = String(text || '').match(/(\d+(?:\.\d+)?)/)
  if (!m) return 0
  let v = parseFloat(m[1])
  if (String(text).includes('万')) v *= 10000
  return v
}

function applySort(rows) {
  const data = [...rows]
  if (activeTab.value === 'newest') {
    return data.sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)))
  }
  if (activeTab.value === 'salary') {
    return data.sort((a, b) => salaryValue(b.salary) - salaryValue(a.salary))
  }
  return data
}

async function loadJobs() {
  loading.value = true
  try {
    const params = { page: 1, size: 20 }
    if (keyword.value) params.keyword = keyword.value
    if (activeDistrict.value) params.district = activeDistrict.value

    const res = await api.get('/jobs/list', { params })
    const rows = Array.isArray(res.data) ? res.data : []
    const sorted = applySort(rows)
    featured.value = sorted[0] || null
    list.value = sorted
  } catch (err) {
    list.value = []
    featured.value = null
    if (window.$toast) window.$toast(err.response?.data?.detail || '岗位加载失败')
  } finally {
    loading.value = false
  }
}

async function loadCities() {
  try {
    const res = await api.get('/meta/cities')
    cities.value = res.data?.list || []
    const hit = cities.value.find((c) => c.id === cityId.value)
    if (hit) cityName.value = hit.name
    else if (cities.value.length) {
      cityId.value = res.data?.default_city_id || cities.value[0].id
      cityName.value = cities.value[0].name
    }
  } catch (err) {
    console.error('城市列表加载失败', err)
  }
}

async function loadDistricts() {
  try {
    const res = await api.get('/meta/districts', { params: { city_id: cityId.value } })
    districts.value = res.data || []
  } catch (err) {
    districts.value = []
  }
}

function openCitySheet() {
  sheetOpen.value = true
}

function chooseCity(city) {
  cityId.value = city.id
  cityName.value = city.name
  localStorage.setItem('guest_city_id', city.id)
  sheetOpen.value = false
  keyword.value = ''
  activeDistrict.value = ''
  localStorage.removeItem('guest_district')
  loadDistricts()
  loadJobs()
}

function chooseDistrict(d) {
  activeDistrict.value = d
  localStorage.setItem('guest_district', d)
  districtOpen.value = false
  reload()
}

function clearDistrict() {
  activeDistrict.value = ''
  localStorage.removeItem('guest_district')
  if (activeTab.value === 'nearby') activeTab.value = 'recommend'
  reload()
}

function switchTab(key) {
  // 附近：先选区镇，再按区镇筛选
  if (key === 'nearby') {
    activeTab.value = 'nearby'
    if (!districts.value.length) loadDistricts()
    if (!activeDistrict.value) {
      districtOpen.value = true
      return
    }
  } else {
    activeTab.value = key
  }
  loadJobs()
}

function reload() {
  loadJobs()
}

function goDetail(id) {
  router.push(`/worker/job-detail/${id}`)
}
function goFind() {
  router.push('/worker/find')
}

onMounted(() => {
  loadCities()
  loadDistricts()
  loadJobs()
})
</script>

<style scoped>
.dz-home {
  --dz-brand: var(--brand, #1677ff);
  --dz-brand-soft: var(--brand-soft, #eaf2ff);
  --dz-bg: var(--bg, #eef1f5);
  --dz-text: var(--text, #1d2531);
  --dz-price: var(--price, #ff7a1a);
  --dz-price-soft: var(--price-soft, #fff1e6);
  min-height: 100vh;
  background: var(--dz-bg);
  padding-bottom: 84px;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* 横幅 */
.dz-hero {
  position: relative;
  padding: 16px 20px 22px;
  background: linear-gradient(165deg, var(--hero-from, #bcdcff) 0%, var(--hero-mid, #d9ecff) 46%, var(--hero-to, #eef4fb) 100%);
  overflow: hidden;
}
.dz-deco {
  position: absolute;
  border-radius: 50%;
  background: var(--dz-price);
  opacity: 0.18;
}
.dz-deco-1 { width: 150px; height: 150px; right: -40px; top: -50px; }
.dz-deco-2 { width: 90px; height: 90px; left: -30px; bottom: -30px; opacity: 0.12; }

.dz-city {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: rgba(255, 255, 255, 0.72);
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 15px;
  font-weight: 700;
  color: #333;
  max-width: 130px;
}
.dz-pin { color: var(--dz-brand); font-size: 13px; }
.dz-city-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dz-caret { font-size: 11px; color: #7b8797; }

.dz-slogan { position: relative; z-index: 2; text-align: center; margin: 18px 0 20px; }
.dz-slogan h1 { font-size: 30px; font-weight: 800; color: #17335c; line-height: 1.2; letter-spacing: 1px; }
.dz-slogan h2 { font-size: 30px; font-weight: 800; color: var(--dz-brand); line-height: 1.2; letter-spacing: 1px; }

.dz-search-row { position: relative; z-index: 2; display: flex; gap: 10px; align-items: center; }
.dz-search {
  flex: 1;
  height: 46px;
  border-radius: 999px;
  background: #fff;
  box-shadow: 0 4px 14px rgba(255, 107, 0, 0.12);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 18px;
}
.dz-search-ico { font-size: 15px; }
.dz-search-input { flex: 1; border: none; background: none; outline: none; font-size: 16px; color: #111; min-width: 0; }
.dz-search-input::placeholder { color: #9aa6b5; }
.dz-search-btn {
  height: 46px;
  padding: 0 22px;
  border-radius: 999px;
  border: none;
  background: var(--dz-brand);
  color: #fff;
  font-size: 16px;
  font-weight: 800;
  flex-shrink: 0;
}

/* 排序胶囊 */
.dz-tabs {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px 4px;
  overflow-x: auto;
  white-space: nowrap;
  scrollbar-width: none;
}
.dz-tabs::-webkit-scrollbar { display: none; }
.dz-tab {
  flex-shrink: 0;
  height: 36px;
  padding: 0 20px;
  border-radius: 999px;
  border: none;
  background: #fff;
  color: #5a6675;
  font-size: 15px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(31, 79, 143, 0.08);
}
.dz-tab.active {
  background: var(--dz-brand);
  color: #fff;
  font-weight: 800;
  box-shadow: 0 4px 12px rgba(255, 107, 0, 0.32);
}
.dz-district-chip {
  flex-shrink: 0;
  font-size: 13px;
  color: var(--dz-brand);
  background: var(--dz-brand-soft);
  padding: 6px 12px;
  border-radius: 999px;
  font-weight: 700;
}

/* 区块 */
.dz-block { padding: 14px 20px 4px; }
.dz-block-head { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 10px; }
.dz-block-head h2 { font-size: 20px; font-weight: 800; color: var(--dz-text); }
.dz-more { font-size: 14px; color: #7b8797; }

.dz-feature {
  display: flex;
  gap: 14px;
  background: #fff;
  border-radius: 18px;
  padding: 14px;
  box-shadow: 0 6px 20px rgba(31, 79, 143, 0.08);
}
.dz-feature-cover {
  position: relative;
  width: 108px;
  height: 108px;
  border-radius: 14px;
  overflow: hidden;
  flex-shrink: 0;
  background: linear-gradient(135deg, #ffe3cc, #ffd0b0);
}
.dz-feature-badge {
  position: absolute;
  left: 0;
  top: 0;
  background: var(--dz-brand);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-bottom-right-radius: 10px;
}
.dz-feature-body { flex: 1; min-width: 0; }
.dz-feature-head { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; margin-bottom: 6px; }
.dz-feature-title { font-size: 20px; font-weight: 800; color: var(--dz-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.dz-price { font-size: 20px; font-weight: 800; color: var(--dz-price); flex-shrink: 0; }
.dz-price.sm { font-size: 17px; }

/* 列表卡片 */
.dz-list { padding: 8px 20px 0; }
.dz-card {
  display: flex;
  gap: 12px;
  background: #fff;
  border-radius: 16px;
  padding: 14px;
  margin-bottom: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}
.dz-card-cover {
  width: 92px;
  height: 92px;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  background: linear-gradient(135deg, #ffe3cc, #ffd0b0);
  display: flex;
  align-items: center;
  justify-content: center;
}
.dz-cover-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.dz-cover-fallback { font-size: 32px; font-weight: 800; color: #fff; text-shadow: 0 2px 6px rgba(0, 0, 0, 0.15); }
.dz-card-body { flex: 1; min-width: 0; }
.dz-card-head { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; margin-bottom: 5px; }
.dz-card-title { font-size: 19px; font-weight: 800; color: var(--dz-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dz-meta { font-size: 13px; color: #7b8797; margin-bottom: 7px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dz-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.dz-tag { background: var(--dz-price-soft); color: var(--dz-price); font-size: 13px; font-weight: 700; padding: 3px 10px; border-radius: 6px; }
.dz-tag.gray { background: var(--dz-bg); color: #555; }

.dz-card-foot { display: flex; align-items: center; gap: 8px; margin-top: 10px; }
.dz-desc {
  flex: 1;
  min-width: 0;
  font-size: 12px;
  color: #8b95a5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dz-look {
  flex-shrink: 0;
  height: 30px;
  padding: 0 14px;
  border-radius: 999px;
  border: none;
  background: var(--dz-price);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
}

.dz-tip { text-align: center; font-size: 14px; color: #9aa6b5; padding: 22px 0 10px; }

/* 我要招人 */
.dz-hire {
  position: fixed;
  right: 16px;
  bottom: 84px;
  z-index: 30;
  height: 42px;
  padding: 0 18px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #ff8a2b, #ff6b00);
  color: #fff;
  font-size: 15px;
  font-weight: 800;
  box-shadow: 0 6px 18px rgba(255, 107, 0, 0.35);
}

/* 弹层 */
.dz-mask { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.42); z-index: 100; display: flex; align-items: flex-end; }
.dz-sheet { width: 100%; background: #fff; border-radius: 20px 20px 0 0; padding: 20px 20px 28px; max-height: 70vh; overflow-y: auto; }
.dz-sheet-head { display: flex; align-items: center; justify-content: space-between; }
.dz-sheet-head h3 { font-size: 20px; font-weight: 800; color: var(--dz-text); }
.dz-sheet-close { font-size: 18px; color: #9aa6b5; padding: 4px; }
.dz-sheet-sub { font-size: 13px; color: #7b8797; margin: 6px 0 16px; }
.dz-city-list { display: flex; flex-direction: column; gap: 10px; }
.dz-city-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 54px;
  padding: 0 18px;
  border-radius: 12px;
  border: 1px solid #eef0f3;
  background: #fff;
  font-size: 17px;
  font-weight: 600;
  color: var(--dz-text);
}
.dz-city-item.active { border-color: var(--dz-brand); background: var(--dz-brand-soft); color: var(--dz-brand); }
</style>
