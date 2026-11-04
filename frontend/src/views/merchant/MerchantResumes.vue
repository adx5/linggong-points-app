<!-- frontend/src/views/merchant/MerchantResumes.vue (B端公共人才库：加入企业认证拦截，修复红线漏洞) -->
<template>
  <div class="talent-page">
    <div class="header">
      <h2>平台人才库</h2>
      <div class="search-bar">
        <input type="text" v-model="keyword" placeholder="搜索意向岗位，如：普工、保洁" />
        <button @click="search">搜索</button>
      </div>
      <div class="filter-tags">
        <span v-for="tag in filters" :key="tag" @click="keyword = tag">{{ tag }}</span>
      </div>
    </div>

    <div class="list">
      <div class="card" v-for="item in talents" :key="item.id" @click="openDetail(item)">
        <div class="info-left">
          <div class="user-title">
            <div class="avatar">{{ item.gender === '男' ? '先' : '女' }}</div>
            <div class="basic">
              <h3>
                {{ item.name }}
                <span class="tag">{{ item.age }}岁</span>
                <span class="tag">{{ item.education }}</span>
              </h3>
              <div class="intent">{{ item.job_intent }} | 期望: {{ item.salary }}</div>
            </div>
          </div>

          <div class="meta-tags">
            <span class="active-time" :class="{ 'today': item.active === '今日活跃' }">{{ item.active }}</span>
            <span class="distance">📍 {{ item.distance }}</span>
            <span class="cloud-tag" v-if="item.is_favorite">⭐ 已入简历库</span>
          </div>
        </div>

        <div class="action-right">
          <button class="btn-call" @click.stop="handleCall(item)">📞 沟通</button>
          <button class="btn-favorite" :class="{ 'is-fav': item.is_favorite }" @click.stop="toggleFavorite(item)">
            {{ item.is_favorite ? '已收藏' : '⭐ 收藏' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <div v-if="showDetail" class="modal-overlay" @click.self="showDetail = false">
      <div class="modal-content">
        <h3>人才详情</h3>
        <div class="detail-info">
          <p><strong>姓名：</strong>{{ currentResume.name }}</p>
          <p><strong>年龄：</strong>{{ currentResume.age }}岁</p>
          <p><strong>学历：</strong>{{ currentResume.education }}</p>
          <p><strong>意向岗位：</strong>{{ currentResume.job_intent }}</p>
          <p><strong>期望薪资：</strong>{{ currentResume.salary }}</p>
        </div>
        <div class="modal-btns">
          <button class="btn-call" @click="handleCall(currentResume)">📞 电话沟通</button>
          <button class="btn-close" @click="showDetail = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const keyword = ref('')
const filters = ['附近优先', '普工', '叉车工', '保安', '保洁', '日结']
const talents = ref([
  { id: 1, name: '张**', age: 28, gender: '男', education: '高中', job_intent: '普工', salary: '5000-6000元', active: '今日活跃', distance: '3.2km', is_favorite: false },
  { id: 2, name: '李**', age: 48, gender: '女', education: '初中', job_intent: '保洁', salary: '3500-4500元', active: '3天前', distance: '8.5km', is_favorite: true },
  { id: 3, name: '王**', age: 24, gender: '男', education: '大专', job_intent: '叉车工', salary: '面议', active: '今日活跃', distance: '1.5km', is_favorite: false }
])

const showDetail = ref(false)
const currentResume = ref({})
const isVerified = ref(false)

// 🚨 核心修复：页面加载时校验企业是否已实名认证
onMounted(async () => {
  try {
    const res = await api.get('/merchant/info')
    if (res.data && res.data.status === 'active') {
      isVerified.value = true
    }
  } catch (err) {
    console.error('获取企业状态失败，可能是未登录或未备案')
  }
})

const openDetail = (item) => {
  currentResume.value = item
  showDetail.value = true
}

const search = () => window.$toast('正在搜索：' + keyword.value)

const toggleFavorite = (item) => {
  // 🚨 拦截：未认证企业禁止收藏
  if (!isVerified.value) {
    return window.$toast('请先完成企业备案认证')
  }
  item.is_favorite = !item.is_favorite
  window.$toast(item.is_favorite ? '已存入企业简历库' : '已从简历库移除')
}

const handleCall = (item) => {
  // 🚨 拦截：未认证企业禁止拨打电话
  if (!isVerified.value) {
    return window.$toast('您的企业尚未通过备案，无法查看联系方式或拨打电话')
  }
  window.$toast('正在拨打...')
}
</script>

<style scoped>
.talent-page { min-height: 100vh; background: #f0f2f5; }
.header { background: #fff; padding: 16px; border-bottom: 1px solid #eee; position: sticky; top: 0; z-index: 99; }
.header h2 { font-size: 18px; color: #1f2937; margin-bottom: 12px; }
.search-bar { display: flex; margin-bottom: 10px; }
.search-bar input { flex: 1; padding: 10px 12px; border: 1px solid #e5e7eb; border-radius: 6px 0 0 6px; font-size: 14px; outline: none; background: #f9fafb; }
.search-bar button { background: #2563eb; color: #fff; padding: 0 20px; border-radius: 0 6px 6px 0; border: none; font-weight: bold; cursor: pointer; }
.filter-tags { display: flex; overflow-x: auto; gap: 8px; padding-bottom: 4px; }
.filter-tags::-webkit-scrollbar { display: none; }
.filter-tags span { white-space: nowrap; font-size: 12px; color: #666; background: #f3f4f6; padding: 4px 10px; border-radius: 12px; cursor: pointer; }
.filter-tags span:first-child { background: #eff6ff; color: #2563eb; font-weight: bold; border: 1px solid #bfdbfe; }

.list { padding: 16px; }
.card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; }
.info-left { flex: 1; padding-right: 12px; }
.user-title { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 10px; }
.avatar { width: 40px; height: 40px; background: #eff6ff; color: #2563eb; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 14px; font-weight: bold; flex-shrink: 0; }
.basic h3 { font-size: 15px; color: #1f2937; margin-bottom: 4px; display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }
.basic h3 .tag { font-size: 11px; background: #f3f4f6; color: #666; padding: 1px 4px; border-radius: 4px; font-weight: normal; }
.intent { font-size: 13px; color: #4b5563; }

.meta-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.active-time, .distance, .cloud-tag { font-size: 11px; padding: 2px 6px; border-radius: 4px; }
.active-time { color: #9ca3af; background: #f9fafb; }
.active-time.today { color: #10b981; background: #ecfdf5; }
.distance { color: #2563eb; background: #eff6ff; }
.cloud-tag { color: #f59e0b; background: #fffbeb; }

.action-right { display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; width: 80px; }
.action-right button { padding: 8px 0; border-radius: 6px; font-size: 12px; font-weight: bold; border: none; cursor: pointer; }
.btn-call { background: #2563eb; color: #fff; }
.btn-favorite { background: #f3f4f6; color: #4b5563; border: 1px solid #e5e7eb !important; }
.btn-favorite.is-fav { background: #fffbeb; color: #f59e0b; border-color: #fde68a !important; }

/* 弹窗样式 */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 999; display: flex; justify-content: center; align-items: center; }
.modal-content { background: #fff; width: 85%; border-radius: 12px; padding: 20px; }
.modal-content h3 { text-align: center; margin-bottom: 20px; font-size: 18px; }
.detail-info { background: #f9fafb; padding: 16px; border-radius: 8px; margin-bottom: 20px; }
.detail-info p { font-size: 14px; color: #333; margin-bottom: 10px; }
.detail-info p:last-child { margin-bottom: 0; }
.modal-btns { display: flex; gap: 10px; }
.modal-btns button { flex: 1; padding: 12px; border-radius: 6px; font-weight: bold; border: none; cursor: pointer; }
.btn-close { background: #f3f4f6; color: #666; }
</style>