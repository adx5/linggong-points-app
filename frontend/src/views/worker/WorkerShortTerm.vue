<!-- frontend/src/views/worker/WorkerShortTerm.vue (C端短期灵活：统一跳转详情页投递) -->
<template>
  <div class="list-page">
    <div class="category-bar">
      <div v-for="item in categories" :key="item.tag" class="cat-card" :class="{ active: currentTag === item.tag }" @click="toggleTag(item.tag)">
        <AppIcon :name="item.iconName" class="icon" />
        <div class="text"><span>{{ item.tag.slice(0, 2) }}</span><span>{{ item.tag.slice(2) }}</span></div>
      </div>
    </div>

    <div class="job-list">
      <div class="card" v-for="job in jobs" :key="job.id" @click="goToDetail(job.id)">
        <div class="info-left">
          <h3>{{ job.title }}</h3>
          <div class="tags"><span>{{ job.filter_tag }}</span></div>
          <p class="loc">📍 {{ job.location }}</p>
        </div>

        <div class="action-right">
          <div class="price">{{ job.salary }}</div>
          <!-- 🚨 修复：点击投递不再直接发请求，而是跳转到详情页统一走选简历流程 -->
          <button class="btn-apply" @click.stop="apply(job.id)">投递</button>
        </div>
      </div>
      <div v-if="jobs.length === 0" class="empty">暂无该分类岗位</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
import AppIcon from '../../components/AppIcon.vue'

const router = useRouter()
const categories = [
  { tag: '日结周结', iconName: 'rijie' }, { tag: '外卖快递', iconName: 'waimei' },
  { tag: '活动促销', iconName: 'huodong' }, { tag: '分拣搬运', iconName: 'fenjian' },
  { tag: '餐饮兼职', iconName: 'canyin' }, { tag: '展会临勤', iconName: 'zhanhui' },
  { tag: '学生假期', iconName: 'xuesheng' }, { tag: '宝妈兼职', iconName: 'baoma' }
]

const currentTag = ref('')
const jobs = ref([])

const loadJobs = async () => {
  try {
    const res = await api.get('/jobs/list', { params: { job_type: 'short_term', filter_tag: currentTag.value } })
    jobs.value = res.data
  } catch (err) { console.error(err) }
}

const toggleTag = (tag) => {
  currentTag.value = currentTag.value === tag ? '' : tag
  loadJobs()
}

const goToDetail = (id) => {
  router.push(`/worker/job-detail/${id}`)
}

// 🚨 核心修复：列表页的投递按钮直接引导去详情页
const apply = (id) => {
  if (!localStorage.getItem('token')) {
    window.$toast('请先登录')
    window.location.hash = '#/login'
    return
  }
  router.push(`/worker/job-detail/${id}`)
}

onMounted(() => { loadJobs() })
</script>

<style scoped>
.list-page { min-height: 100vh; background: #f5f6f8; }
.category-bar { display: flex; align-items: flex-end; background: #fff; padding: 12px 18px; border-bottom: 1px solid #eee; position: sticky; top: 0; z-index: 99; box-shadow: 0 2px 6px rgba(0,0,0,0.03); }
.cat-card { flex: 1; margin: 0 3px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 8px 0; background: #f5f6f8; border-radius: 6px; cursor: pointer; transition: all 0.3s; }
.cat-card .icon { font-size: 16px; margin-bottom: 6px; }
.cat-card .text { display: flex; flex-direction: column; align-items: center; font-size: 10px; color: #4b5563; line-height: 1.3; white-space: nowrap; }
.cat-card.active { flex: 1.8; background: #2563eb; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); transform: translateY(-3px); }
.cat-card.active .text { color: #fff; font-size: 13px; font-weight: bold; line-height: 1.5; }

.job-list { padding: 12px; }
.card { background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; }
.info-left { flex: 1; padding-right: 12px; }
.info-left h3 { font-size: 16px; color: #1f2937; margin-bottom: 8px; }
.tags { display: flex; gap: 6px; margin-bottom: 8px; }
.tags span { background: #eff6ff; color: #2563eb; font-size: 11px; padding: 2px 6px; border-radius: 4px; }
.loc { font-size: 12px; color: #9ca3af; margin: 0; }

.action-right { display: flex; flex-direction: column; align-items: flex-end; gap: 12px; flex-shrink: 0; }
.price { color: #ef4444; font-weight: bold; font-size: 15px; text-align: right; }
.btn-apply { background: #2563eb; color: #fff; padding: 6px 16px; border-radius: 6px; font-weight: bold; font-size: 13px; border: none; cursor: pointer; }

.empty { text-align: center; padding: 40px; color: #999; }
</style>