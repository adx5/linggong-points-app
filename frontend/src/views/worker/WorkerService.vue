<!-- frontend/src/views/worker/WorkerService.vue —— 大字版 P5 同城服务页
     设计来源：0暂放资料/UI橙色大字  C端求职.html P6
     结构：定位搜索 + 类目金刚区(6) + 师傅列表卡片
-->
<template>
  <div class="sv-page">
    <header class="sv-top">
      <div v-if="menuOpen" class="sv-menu-mask" @click="menuOpen = false"></div>

      <div class="sv-top-row">
        <div class="sv-city-wrap">
          <button class="sv-city" @click.stop="toggleDistrictMenu">
            <span class="sv-pin">◎</span>
            <span class="sv-city-name">{{ activeDistrict || cityName }}</span>
            <span class="sv-caret" :class="{ up: menuOpen }">▾</span>
          </button>

          <div v-if="menuOpen" class="sv-city-menu">
            <button
              v-for="opt in districtOptions"
              :key="opt.value || 'all'"
              :class="['sv-menu-item', { active: opt.value === activeDistrict }]"
              @click.stop="chooseDistrict(opt.value)"
            >
              <span>{{ opt.label }}</span>
              <span v-if="opt.value === activeDistrict" class="sv-menu-check">✓</span>
            </button>
            <p v-if="!districts.length" class="sv-menu-empty">暂无区/镇</p>
          </div>
        </div>

        <div class="sv-search">
          <span class="sv-search-ico">🔍</span>
          <input v-model="keyword" class="sv-search-input" placeholder="搜索：保洁、维修、搬家" @keyup.enter="loadProviders" />
          <button v-if="keyword" class="sv-clear" @click="clearKeyword">✕</button>
        </div>
      </div>

      <!-- 滚动后：类目收成一行文字标签（吸顶） -->
      <div v-show="collapsed" class="sv-strip">
        <button
          v-for="c in categories"
          :key="c.id"
          :class="['sv-strip-item', { on: activeCategory === c.id }]"
          @click="pickCategory(c.id)"
        >
          {{ c.name }}
        </button>
      </div>
    </header>

    <!-- 类目（仅未折叠时显示） -->
    <section v-show="!collapsed" class="sv-cats">
      <button
        v-for="c in categories"
        :key="c.id"
        :class="['sv-cat', { on: activeCategory === c.id }]"
        @click="pickCategory(c.id)"
      >
        <span class="sv-cat-ico">{{ c.icon || '🛠️' }}</span>
        <span class="sv-cat-label">{{ c.name }}</span>
      </button>
    </section>

    <!-- 师傅列表 -->
    <section class="sv-list">
      <div class="sv-list-head">
        <h2>附近师傅</h2>
        <span class="sv-count">{{ list.length }} 位</span>
      </div>

      <article v-for="p in list" :key="p.id" class="sv-card" @click="goDetail(p.id)">
        <div class="sv-avatar">{{ (p.display_name || '师')[0] }}</div>
        <div class="sv-body">
          <div class="sv-name-row">
            <h3 class="sv-name">{{ p.display_name }}</h3>
            <span class="sv-rating">★ {{ p.rating }}</span>
          </div>
          <p class="sv-meta">{{ p.category_name }} · {{ p.district }} · 已服务 {{ p.orders_done }} 单</p>
          <p class="sv-svc">
            <span v-if="p.min_price !== null && p.min_price !== undefined" class="sv-price">￥{{ p.min_price }} 起</span>
            <span v-if="p.service_count" class="sv-svc-count">{{ p.service_count }} 项服务</span>
            <span v-else class="sv-svc-count muted">暂未上架服务</span>
          </p>
          <p class="sv-intro">{{ p.intro }}</p>
          <div class="sv-foot">
            <span class="sv-tag">平台保障</span>
            <span class="sv-tag gray">{{ p.verify_status === 'verified' ? '已认证' : '待认证' }}</span>
            <button class="sv-btn">查看详情 ›</button>
          </div>
        </div>
      </article>

      <p v-if="loading" class="sv-tip">正在加载…</p>
      <p v-else-if="!list.length" class="sv-tip">该分类下暂无师傅，换个分类看看</p>
      <p v-else class="sv-tip">— 已经到底了 —</p>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()

const categories = ref([])
const list = ref([])
const keyword = ref('')
const activeCategory = ref(null)
const loading = ref(false)

const cityId = ref(localStorage.getItem('guest_city_id') || '410185')
const cityNameMap = { 410185: '登封', 410173: '航空港', 411300: '南阳' }
const cityName = ref(cityNameMap[cityId.value] || '登封')

// 当前城市的下一级区/镇筛选（就地下拉，不弹全屏）
const districts = ref([])
const activeDistrict = ref('')
const menuOpen = ref(false)

const districtOptions = computed(() => [
  { value: '', label: `全部（${cityName.value}）` },
  ...districts.value.map((d) => ({ value: d, label: d }))
])

async function loadCategories() {
  try {
    const res = await api.get('/services/categories')
    categories.value = res.data || []
  } catch (err) {
    categories.value = []
  }
}

async function toggleDistrictMenu() {
  menuOpen.value = !menuOpen.value
  if (menuOpen.value && !districts.value.length) await loadDistricts()
}

async function loadDistricts() {
  try {
    const res = await api.get('/meta/districts', { params: { city_id: cityId.value } })
    districts.value = res.data || []
  } catch (err) {
    districts.value = []
  }
}

function chooseDistrict(d) {
  activeDistrict.value = d
  menuOpen.value = false
  loadProviders()
}

async function loadProviders() {
  loading.value = true
  try {
    const params = { page: 1, size: 20 }
    if (activeCategory.value) params.category_id = activeCategory.value
    if (keyword.value) params.keyword = keyword.value
    if (activeDistrict.value) params.district = activeDistrict.value
    const res = await api.get('/services/providers', { params })
    list.value = res.data || []
  } catch (err) {
    list.value = []
    if (window.$toast) window.$toast(err.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

function pickCategory(id) {
  activeCategory.value = activeCategory.value === id ? null : id
  loadProviders()
}

function clearKeyword() {
  keyword.value = ''
  loadProviders()
}

function goDetail(id) {
  router.push(`/worker/service-detail/${id}`)
}

// 滚动折叠：类目金刚区收起为一行文字标签
const collapsed = ref(false)
const COLLAPSE_AT = 88

function onScroll() {
  collapsed.value = window.scrollY > COLLAPSE_AT
}

onMounted(() => {
  loadDistricts()
  loadCategories()
  loadProviders()
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
})
</script>

<style scoped>
.sv-page {
  min-height: 100vh;
  background: var(--bg, #eef1f5);
  padding-bottom: 20px;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.sv-top { position: sticky; top: 0; z-index: 20; background: #fff; padding: 14px 20px 12px; box-shadow: 0 2px 8px rgba(0,0,0,.03); }

/* 城市 + 搜索同一行 */
.sv-top-row { display: flex; align-items: center; gap: 10px; }
.sv-city {
  display: flex;
  align-items: center;
  gap: 3px;
  border: none;
  background: none;
  padding: 0;
  flex-shrink: 0;
  max-width: 96px;
}
.sv-pin { color: var(--price, #ff7a1a); font-size: 13px; }
.sv-city-name { font-size: 17px; font-weight: 800; color: #111; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sv-caret { font-size: 11px; color: #7b8797; }

.sv-search { flex: 1; display: flex; align-items: center; gap: 8px; height: 44px; padding: 0 16px; background: var(--bg); border-radius: 999px; min-width: 0; }
.sv-search-ico { font-size: 15px; }
.sv-search-input { flex: 1; border: none; background: none; outline: none; font-size: 16px; color: #111; min-width: 0; }
.sv-clear { border: none; background: #dfe5ee; color: #fff; width: 20px; height: 20px; border-radius: 50%; font-size: 12px; }

/* 折叠后的文字标签条（吸顶） */
.sv-strip {
  display: flex;
  gap: 18px;
  padding: 8px 0 10px;
  margin-top: 10px;
  overflow-x: auto;
  white-space: nowrap;
  border-top: 1px solid #f2f4f7;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.sv-strip::-webkit-scrollbar { display: none; }
.sv-strip-item {
  flex-shrink: 0;
  border: none;
  background: none;
  padding: 0;
  font-size: 15px;
  font-weight: 700;
  color: #333;
}
.sv-strip-item.on { color: var(--price, #ff7a1a); }

.sv-cats { display: flex; flex-wrap: wrap; background: #fff; padding: 16px 10px 18px; margin-bottom: 12px; }
.sv-cat { width: 33.33%; border: none; background: none; display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 6px 0; }
.sv-cat-ico { width: 50px; height: 50px; border-radius: 16px; background: #f9fafc; display: flex; align-items: center; justify-content: center; font-size: 24px; }
.sv-cat-label { font-size: 14px; font-weight: 700; color: #333; }
.sv-cat.on .sv-cat-ico { background: var(--price-soft, #fff1e6); border: 1px solid var(--price, #ff7a1a); }
.sv-cat.on .sv-cat-label { color: var(--price, #ff7a1a); }

.sv-list { padding: 0 20px; }
.sv-list-head { display: flex; align-items: baseline; justify-content: space-between; margin: 6px 0 12px; }
.sv-list-head h2 { font-size: 20px; font-weight: 800; color: #111; }
.sv-count { font-size: 13px; color: #7b8797; }

.sv-card { display: flex; gap: 12px; background: #fff; border-radius: 16px; padding: 14px; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(0,0,0,.04); }
.sv-avatar {
  width: 60px; height: 60px; border-radius: 16px; flex-shrink: 0;
  background: linear-gradient(135deg, #ffd6b0, #ffb27a);
  color: #fff; font-size: 24px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
}
.sv-body { flex: 1; min-width: 0; }
.sv-name-row { display: flex; align-items: baseline; justify-content: space-between; }
.sv-name { font-size: 19px; font-weight: 800; color: #111; }
.sv-rating { font-size: 15px; font-weight: 800; color: var(--price, #ff7a1a); }
.sv-meta { font-size: 13px; color: #7b8797; margin: 4px 0 6px; }
.sv-svc { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.sv-price { font-size: 15px; font-weight: 800; color: var(--price, #ff7a1a); }
.sv-svc-count { font-size: 12px; color: #7b8797; background: var(--bg); padding: 2px 8px; border-radius: 6px; }
.sv-svc-count.muted { color: #b9c2cc; }
.sv-intro { font-size: 13px; color: #4a5565; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.sv-foot { display: flex; align-items: center; gap: 8px; margin-top: 10px; }
.sv-tag { background: var(--price-soft, #fff1e6); color: var(--price, #ff7a1a); font-size: 12px; font-weight: 700; padding: 3px 9px; border-radius: 6px; }
.sv-tag.gray { background: var(--bg, #eef1f5); color: #555; }
.sv-btn { margin-left: auto; border: none; background: var(--price, #ff7a1a); color: #fff; font-size: 13px; font-weight: 700; height: 32px; padding: 0 14px; border-radius: 999px; }

.sv-tip { text-align: center; font-size: 14px; color: #9aa6b5; padding: 22px 0; }

/* 区/镇：就地下拉菜单 */
.sv-menu-mask { position: fixed; inset: 0; z-index: 1; background: transparent; }
.sv-city-wrap { position: relative; z-index: 2; flex-shrink: 0; }
.sv-caret { transition: transform 0.18s ease; }
.sv-caret.up { transform: rotate(180deg); }

.sv-city-menu {
  position: absolute;
  top: 34px;
  left: -8px;
  z-index: 10;
  min-width: 168px;
  max-height: 260px;
  overflow-y: auto;
  background: #fff;
  border-radius: 12px;
  padding: 6px;
  box-shadow: 0 10px 28px rgba(31, 79, 143, 0.16);
  border: 1px solid #eef0f3;
}
.sv-menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border: none;
  background: none;
  padding: 11px 12px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #333;
  text-align: left;
  white-space: nowrap;
}
.sv-menu-item.active { color: var(--brand); background: var(--brand-soft); font-weight: 800; }
.sv-menu-check { color: var(--brand); font-weight: 900; }
.sv-menu-empty { text-align: center; font-size: 13px; color: #9aa6b5; padding: 10px 0; }
</style>
