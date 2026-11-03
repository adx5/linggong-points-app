<!-- (C端首页：顶部广告位Banner + 最新热招) -->
<template>
  <div class="home-page">
    <div class="header">
      <h2>XX零工市场</h2>
      <div class="search-bar" @click="$router.push('/worker/find')">
        <span>🔍 搜索岗位 / 单位</span>
      </div>
    </div>

    <div class="banner-area">
      <div class="banner-item">
        <div class="banner-content">
          <h3>同城好工作</h3>
          <p>真实岗位 · 即时结算 · 政府监管</p>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">
        <h3>最新热招</h3>
        <span @click="$router.push('/worker/find')">更多 ></span>
      </div>
      <div class="job-list">
        <!-- 🚨 点击卡片跳转详情 -->
        <div class="job-card" v-for="job in jobs" :key="job.id" @click="goToDetail(job.id)">
          <div class="row">
            <h4>{{ job.title }}</h4>
            <span class="price">{{ job.salary }}</span>
          </div>
          <p class="loc">📍 {{ job.location }}</p>
          <!-- 阻止冒泡，防止点投递时跳详情 -->
          <button class="btn-apply" @click.stop="apply(job.id)">在线投递</button>
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
const jobs = ref([])

const loadJobs = async () => {
  try {
    const res = await api.get('/jobs/list')
    jobs.value = res.data.slice(0, 3)
  } catch (err) {
    console.error(err)
  }
}

const goToDetail = (id) => {
  router.push(`/worker/job-detail/${id}`)
}

const apply = async (id) => {
  try {
    window.$toast((await api.post(`/jobs/apply/${id}`)).message)
  } catch (err) {
    window.$toast(err.response?.data?.detail || '投递失败')
  }
}

onMounted(() => { loadJobs() })
</script>

<style scoped>
.home-page { min-height: 100vh; background: #f5f6f8; }
.header { background: #2563eb; padding: 20px 16px 60px; color: #fff; }
.header h2 { margin-bottom: 15px; font-size: 20px; }
.search-bar { background: #fff; color: #999; padding: 10px 15px; border-radius: 8px; font-size: 14px; }
.banner-area { margin: -40px 12px 12px; position: relative; z-index: 10; }
.banner-item { height: 140px; background: linear-gradient(135deg, #3b82f6, #2dd4bf); border-radius: 12px; display: flex; align-items: center; padding: 0 24px; color: #fff; box-shadow: 0 4px 12px rgba(37,99,235,0.2); }
.banner-content h3 { font-size: 22px; margin-bottom: 8px; font-weight: bold; }
.banner-content p { font-size: 13px; opacity: 0.9; }
.section { padding: 0 12px; }
.section-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-title h3 { font-size: 16px; }
.section-title span { font-size: 12px; color: #999; }
.job-card { background: #fff; border-radius: 8px; padding: 15px; margin-bottom: 12px; }
.row { display: flex; justify-content: space-between; margin-bottom: 8px; }
.price { color: #ef4444; font-weight: bold; }
.loc { font-size: 12px; color: #666; margin-bottom: 12px; }
.btn-apply { width: 100%; background: #2563eb; color: #fff; padding: 10px; border-radius: 6px; font-size: 14px; border: none; cursor: pointer; }
</style>