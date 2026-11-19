<!-- frontend/src/views/worker/WorkerFavorites.vue —— 我的收藏（本地存储） -->
<template>
  <div class="fav-page">
    <header class="fav-nav">
      <button class="fav-back" @click="$router.back()">‹</button>
      <span class="fav-title">我的收藏</span>
      <span class="fav-count">{{ jobs.length }}</span>
    </header>

    <div v-if="loading" class="fav-tip">加载中…</div>

    <template v-else>
      <article v-for="job in jobs" :key="job.id" class="fav-card" @click="goDetail(job.id)">
        <div class="fav-body">
          <div class="fav-head">
            <h3 class="fav-name">{{ job.title }}</h3>
            <span class="fav-price">{{ job.salary }}</span>
          </div>
          <p class="fav-meta">◎ {{ job.location }}<template v-if="job.company_name"> · {{ job.company_name }}</template></p>
          <div class="fav-tags">
            <span class="fav-tag">{{ job.filter_tag || '日结' }}</span>
            <span class="fav-tag gray">{{ job.job_type === 'long_term' ? '长期' : '短期' }}</span>
          </div>
        </div>
        <button class="fav-del" @click.stop="remove(job.id)">取消收藏</button>
      </article>

      <p v-if="!jobs.length" class="fav-tip">
        还没有收藏的岗位，去「找活」看看，点详情页的「收藏」即可
      </p>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
import { getFavoriteIds, toggleFavorite } from '../../utils/favorites'

const router = useRouter()
const jobs = ref([])
const loading = ref(true)

async function load() {
  const ids = getFavoriteIds()
  if (!ids.length) {
    jobs.value = []
    loading.value = false
    return
  }

  loading.value = true
  const results = await Promise.allSettled(ids.map((id) => api.get(`/jobs/${id}`)))
  jobs.value = results
    .filter((r) => r.status === 'fulfilled' && r.value?.data?.job)
    .map((r) => {
      const job = r.value.data.job
      const company = r.value.data.company || {}
      return { ...job, company_name: company.company_name }
    })
  loading.value = false
}

function remove(id) {
  toggleFavorite(id)
  jobs.value = jobs.value.filter((j) => String(j.id) !== String(id))
  window.$toast && window.$toast('已取消收藏')
}

function goDetail(id) {
  router.push(`/worker/job-detail/${id}`)
}

onMounted(load)
</script>

<style scoped>
.fav-page { min-height: 100vh; background: var(--bg, #eef1f5); padding-bottom: 30px; }

.fav-nav {
  position: sticky;
  top: 0;
  z-index: 10;
  height: 52px;
  background: #fff;
  display: flex;
  align-items: center;
  padding: 0 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}
.fav-back { border: none; background: none; font-size: 28px; width: 40px; text-align: left; color: #333; padding-bottom: 4px; }
.fav-title { flex: 1; text-align: center; font-size: 18px; font-weight: 800; color: var(--text, #111); }
.fav-count { width: 40px; text-align: right; font-size: 13px; color: #9aa6b5; }

.fav-card {
  position: relative;
  background: #fff;
  border-radius: 16px;
  padding: 16px 18px;
  margin: 12px 20px 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}
.fav-head { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; }
.fav-name { font-size: 18px; font-weight: 800; color: var(--text, #111); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fav-price { font-size: 17px; font-weight: 800; color: var(--price, #ff7a1a); flex-shrink: 0; }
.fav-meta { font-size: 13px; color: #7b8797; margin: 6px 0 10px; }
.fav-tags { display: flex; gap: 8px; }
.fav-tag { background: var(--price-soft, #fff1e6); color: var(--price, #ff7a1a); font-size: 12px; font-weight: 700; padding: 3px 9px; border-radius: 6px; }
.fav-tag.gray { background: var(--bg, #eef1f5); color: #555; }

.fav-del {
  margin-top: 12px;
  height: 36px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid #eef0f3;
  background: #fff;
  color: #7b8797;
  font-size: 13px;
  font-weight: 700;
}

.fav-tip { text-align: center; font-size: 14px; color: #9aa6b5; padding: 40px 30px; line-height: 1.7; }
</style>
