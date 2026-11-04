<!-- frontend/src/views/worker/WorkerShortTerm.vue (字体暴力加大加粗版) -->
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

const apply = (id) => {
  if (!localStorage.getItem('token')) {
    window.$toast('请先登录')
    window.location.hash = '#/login'
    return
  }
  window.$toast('请在详情页选择简历并投递')
  router.push(`/worker/job-detail/${id}`)
}

onMounted(() => { loadJobs() })
</script>

<style scoped>
.list-page { min-height: 100vh; background: #f5f6f8; }
.category-bar { display: flex; align-items: flex-end; background: linear-gradient(135deg, #3b82f6, #2dd4bf); padding: 16px 12px; border-bottom: none; position: sticky; top: 0; z-index: 99; box-shadow: 0 4px 12px rgba(45, 212, 191, 0.3); }
.cat-card { flex: 1; margin: 0 2px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 10px 0; background: rgba(255, 255, 255, 0.15); border-radius: 8px; cursor: pointer; transition: all 0.3s; }
.cat-card .icon { font-size: 20px; margin-bottom: 6px; }

/* 🚨 核心修改：未选中字体加大加粗 */
.cat-card .text {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 14px;
  font-weight: bold;
  color: #ffffff;
  line-height: 1.2;
  white-space: nowrap;
  opacity: 0.95;
}

.cat-card.active { flex: 1.8; background: #ffffff; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); transform: translateY(-3px); }

/* 🚨 核心修改：选中字体进一步加大，使用极粗体 */
.cat-card.active .text {
  color: #2563eb;
  font-size: 16px;
  font-weight: 900;
  line-height: 1.4;
  opacity: 1;
}

.job-list { padding: 12px; }
.card { background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
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