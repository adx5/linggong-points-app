<!-- (Admin工作台：政务蓝白风数据大盘，全量待办) -->
<template>
  <div class="admin-dash">
    <div class="header">
      <div class="header-top">
        <div class="title-area">
          <h2>{{ pageTitle }}</h2>
          <p>{{ subTitle }}</p>
        </div>
        <div class="mine-entry" @click="$router.push('/admin/mine')">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        </div>
      </div>
    </div>

    <!-- 顶部 3 个数据 -->
    <div class="stats-card">
      <div class="stat-item">
        <div class="val">{{ stats.total_users }}</div>
        <div class="label">总注册用户</div>
      </div>
      <div class="stat-item">
        <div class="val text-blue">{{ stats.total_jobs }}</div>
        <div class="label">总发布岗位</div>
      </div>
      <div class="stat-item">
        <div class="val text-red">{{ totalTodo }}</div>
        <div class="label">总待办事项</div>
      </div>
    </div>

    <!-- 🚨 第一块：资质审核待办 -->
    <div class="menu-card">
      <h3>资质审核待办</h3>
      <div class="todo-item" @click="$router.push('/admin/audit')">
        <span>🏢 企业备案待审 <b class="text-red">{{ todoCounts.company }}</b> 家</span>
        <span class="arrow">></span>
      </div>
      <div class="todo-item" @click="$router.push('/admin/audit')">
        <span>🕵️ 经纪人资质待审 <b class="text-red">{{ todoCounts.agent }}</b> 人</span>
        <span class="arrow">></span>
      </div>
      <div class="todo-item" @click="$router.push('/admin/audit')">
        <span>🔧 服务商资质待审 <b class="text-red">{{ todoCounts.provider }}</b> 家</span>
        <span class="arrow">></span>
      </div>
    </div>

    <!-- 🚨 第二块：岗位风控待办 -->
    <div class="menu-card">
      <h3>岗位风控待办</h3>
      <div class="todo-item" @click="$router.push('/admin/risk')">
        <span>🤖 AI 语义预警 <b class="text-orange">{{ todoCounts.aiRisk }}</b> 条</span>
        <span class="arrow">></span>
      </div>
      <div class="todo-item" @click="$router.push('/admin/risk')">
        <span>⚠️ 信息举报待核实 <b class="text-red">{{ todoCounts.report }}</b> 条</span>
        <span class="arrow">></span>
      </div>
      <div class="todo-item" @click="$router.push('/admin/risk')">
        <span>📞 违规处理跟踪回访 <b class="text-blue">{{ todoCounts.revisit }}</b> 条</span>
        <span class="arrow">></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../../api'

const role = ref(localStorage.getItem('activeRole') || 'ops')
const pageTitle = computed(() => role.value === 'gov' ? '合规与监管工作台' : '平台运营工作台')
const subTitle = computed(() => role.value === 'gov' ? '欢迎您，合规审核专员' : '欢迎您，平台运营专员')

// 基础数据
const stats = ref({ total_users: 0, total_jobs: 0 })

// 🚨 模拟全量待办数据（演示用）
const todoCounts = ref({
  company: 1, agent: 2, provider: 1,
  aiRisk: 1, report: 2, revisit: 1
})

const totalTodo = computed(() => {
  return todoCounts.value.company + todoCounts.value.agent + todoCounts.value.provider +
         todoCounts.value.aiRisk + todoCounts.value.report + todoCounts.value.revisit
})

onMounted(async () => {
  try {
    const res = await api.get('/admin/stats')
    stats.value = res.data
    // 实际场景下，待办数量由后端接口返回，这里暂时用 Mock
    // todoCounts.value = res.todoCounts
  } catch (err) {}
})
</script>

<style scoped>
.admin-dash { min-height: 100vh; background: #f0f4f8; padding-bottom: 80px; }
.header { background: #0052d9; padding: 30px 20px 40px; color: #ffffff; border-radius: 0 0 20px 20px; }
.header-top { display: flex; justify-content: space-between; align-items: flex-start; }
.title-area h2 { font-size: 22px; margin-bottom: 8px; }
.title-area p { font-size: 13px; opacity: 0.8; }
.mine-entry { width: 36px; height: 36px; background: rgba(255,255,255,0.2); border-radius: 50%; display: flex; justify-content: center; align-items: center; cursor: pointer; }
.mine-entry:active { background: rgba(255,255,255,0.3); }

.stats-card { display: flex; background: #ffffff; margin: -20px 16px 16px; border-radius: 12px; padding: 20px; position: relative; z-index: 10; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.stat-item { flex: 1; text-align: center; border-right: 1px solid #f3f4f6; }
.stat-item:last-child { border-right: none; }
.stat-item .val { font-size: 24px; font-weight: bold; color: #333333; margin-bottom: 4px; }
.stat-item .val.text-blue { color: #0052d9; }
.stat-item .val.text-red { color: #ef4444; }
.stat-item .label { font-size: 12px; color: #6b7280; }

.menu-card { background: #ffffff; margin: 16px; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
.menu-card h3 { font-size: 15px; margin-bottom: 12px; color: #333333; font-weight: bold; }
.todo-item { display: flex; justify-content: space-between; padding: 16px 0; border-top: 1px solid #f3f4f6; font-size: 14px; color: #4b5563; cursor: pointer; }
.todo-item:active { background: #f9fafb; }
.arrow { color: #9ca3af; }
b.text-red { color: #ef4444; }
b.text-orange { color: #f59e0b; }
b.text-blue { color: #0052d9; }
</style>