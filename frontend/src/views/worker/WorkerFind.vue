<!-- (C端找活大厅：左右布局，释放信息空间) -->
<template>
  <div class="find-page">
    <div class="search-box">
      <input type="text" v-model="keyword" placeholder="请输入工作名称" @keyup.enter="handleSearch" />
      <button @click="handleSearch">搜索</button>
    </div>

    <div class="list" ref="scrollContainer" @scroll="handleScroll">
      <div class="card" v-for="job in jobs" :key="job.id" @click="goToDetail(job.id)">
        <!-- 左侧信息流 -->
        <div class="info-left">
          <div class="title-row">
            <h3>{{ job.title }}</h3>
          </div>
          <div class="tags">
            <span v-for="tag in job.tags.split(',')" :key="tag">{{ tag }}</span>
          </div>
          <p class="loc">📍 {{ job.location }}</p>
        </div>

        <!-- 右侧操作与薪资 -->
        <div class="action-right">
          <div class="price">{{ job.salary }}</div>
          <button class="btn-apply" @click.stop="apply(job.id)">投递</button>
        </div>
      </div>

      <div v-if="jobs.length === 0 && !loading" class="empty">暂无岗位，去其他板块看看吧</div>
      <div v-if="loading" class="loading-text">加载中...</div>
      <div v-if="noMore && jobs.length > 0" class="loading-text">没有更多岗位了~</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()
const keyword = ref('')
const jobs = ref([])
const page = ref(1)
const size = 10
const loading = ref(false)
const noMore = ref(false)
const scrollContainer = ref(null)

const goToDetail = (id) => router.push(`/worker/job-detail/${id}`)

const loadJobs = async (isAppend = false) => {
  if (loading.value) return
  loading.value = true
  try {
    const res = await api.get('/jobs/list', { params: { keyword: keyword.value, page: page.value, size: size } })
    const newJobs = res.data || []
    if (isAppend) jobs.value = [...jobs.value, ...newJobs]
    else jobs.value = newJobs
    noMore.value = jobs.value.length >= res.total
  } catch (err) { console.error(err) } finally { loading.value = false }
}

const handleSearch = () => { page.value = 1; noMore.value = false; loadJobs(false) }
const handleScroll = (e) => {
  const el = e.target
  if (el.scrollHeight - el.scrollTop - el.clientHeight < 20) {
    if (!loading.value && !noMore.value) { page.value++; loadJobs(true) }
  }
}

const apply = async (id) => {
  try {
    const res = await api.post(`/jobs/apply/${id}`)
    window.$toast(res.message)
  } catch (err) { window.$toast(err.response?.data?.detail || '投递失败') }
}

onMounted(() => { loadJobs() })
</script>

<style scoped>
.find-page { height: 100vh; display: flex; flex-direction: column; background: #f5f6f8; }
.search-box { display: flex; padding: 12px; background: #fff; flex-shrink: 0; }
.search-box input { flex: 1; padding: 10px; background: #f3f4f6; border-radius: 6px 0 0 6px; font-size: 14px; outline: none; border: none; }
.search-box button { background: #2563eb; color: #fff; padding: 0 20px; border-radius: 0 6px 6px 0; font-weight: bold; border: none; cursor: pointer; }
.list { flex: 1; overflow-y: auto; padding: 12px; }

/* 🚨 核心：左右 Flex 布局 */
.card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center; /* 垂直居中 */
}

/* 左侧信息区 */
.info-left { flex: 1; padding-right: 12px; }
.title-row h3 { font-size: 16px; color: #1f2937; margin-bottom: 8px; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.tags span { background: #f3f4f6; font-size: 11px; padding: 2px 6px; border-radius: 4px; color: #666; }
.loc { font-size: 12px; color: #9ca3af; margin: 0; }

/* 右侧操作区 */
.action-right { display: flex; flex-direction: column; align-items: flex-end; gap: 12px; flex-shrink: 0; }
.price { color: #ef4444; font-weight: bold; font-size: 15px; text-align: right; }
.btn-apply { background: #2563eb; color: #fff; padding: 6px 16px; border-radius: 6px; font-weight: bold; font-size: 13px; border: none; cursor: pointer; }

.empty { text-align: center; padding: 40px; color: #999; }
.loading-text { text-align: center; font-size: 12px; color: #999; padding: 10px 0; }
</style>