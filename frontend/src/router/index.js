// frontend/src/router/index.js (路由配置：修复根路由重定向，放行游客)
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 🚨 修复点 1：默认重定向到求职者首页（现在游客也能看）
    { path: '/', redirect: '/worker/home' },
    { path: '/login', component: () => import('../views/Login.vue') },

    // ================= C端 (求职者) =================
    {
      path: '/worker',
      component: () => import('../layout/WorkerLayout.vue'),
      meta: { role: 'worker' },
      children: [
        { path: 'home', component: () => import('../views/worker/WorkerHome.vue') },
        { path: 'long-term', component: () => import('../views/worker/WorkerLongTerm.vue') },
        { path: 'short-term', component: () => import('../views/worker/WorkerShortTerm.vue') },
        { path: 'find', component: () => import('../views/worker/WorkerFind.vue') },
        { path: 'job-detail/:id', component: () => import('../views/worker/JobDetail.vue') },
        // 以下页面必须登录
        { path: 'my-applies', component: () => import('../views/worker/WorkerMyApplies.vue'), meta: { requireAuth: true } },
        { path: 'task', component: () => import('../views/worker/WorkerTask.vue'), meta: { requireAuth: true } },
        { path: 'exchange', component: () => import('../views/worker/WorkerExchange.vue'), meta: { requireAuth: true } },
        { path: 'mine', component: () => import('../views/worker/WorkerMine.vue'), meta: { requireAuth: true } }
      ]
    },

    // ================= B端 (企业/招聘方) =================
    {
      path: '/merchant',
      component: () => import('../layout/MerchantLayout.vue'),
      meta: { role: 'merchant', requireAuth: true },
      children: [
        { path: 'dash', component: () => import('../views/merchant/MerchantDash.vue') },
        { path: 'job-list', component: () => import('../views/merchant/MerchantJobList.vue') },
        { path: 'talent-pool', component: () => import('../views/merchant/MerchantResumes.vue') },
        { path: 'received-resumes', component: () => import('../views/merchant/MerchantTalentPool.vue') },
        { path: 'interviews', component: () => import('../views/merchant/MerchantInterviewSchedule.vue') },
        { path: 'reviews', component: () => import('../views/merchant/MerchantSettlement.vue') },
        { path: 'messages', component: () => import('../views/merchant/MerchantMessages.vue') },
        { path: 'settings', component: () => import('../views/merchant/MerchantSettings.vue') },
        { path: 'mine', component: () => import('../views/merchant/MerchantMine.vue') },
        { path: 'company', component: () => import('../views/merchant/MerchantCompany.vue') }
      ]
    },
    { path: '/merchant/job-create', component: () => import('../views/merchant/MerchantJobs.vue'), meta: { role: 'merchant', requireAuth: true } },
    { path: '/merchant/info', component: () => import('../views/merchant/MerchantInfo.vue'), meta: { role: 'merchant', requireAuth: true } },
    { path: '/merchant/verify', component: () => import('../views/merchant/MerchantVerify.vue'), meta: { role: 'merchant', requireAuth: true } },

    // ================= Admin端 =================
    {
      path: '/admin',
      component: () => import('../layout/AdminLayout.vue'),
      meta: { requireAuth: true },
      children: [
        { path: 'dash', component: () => import('../views/admin/AdminDash.vue') },
        { path: 'audit', component: () => import('../views/admin/AuditCenter.vue') },
        { path: 'risk', component: () => import('../views/admin/RiskControl.vue') },
        { path: 'gov', component: () => import('../views/admin/GovDashboard.vue') },
        { path: 'mine', component: () => import('../views/admin/AdminMine.vue') }
      ]
    }
  ]
})

// ================= 全局路由守卫 =================
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const activeRole = localStorage.getItem('activeRole')

  if (to.path === '/login') return next()

  // 判断该页面是否强制要求登录
  const requireAuth = to.matched.some(record => record.meta.requireAuth)

  // 如果没 Token 且要求登录，拦截
  if (!token && requireAuth) {
    if (window.$toast) window.$toast('请先登录')
    window.location.href = '/login'
    return
  }

  // 如果有 Token，校验角色
  if (token) {
    const requiredRole = to.matched.find(record => record.meta.role)?.meta.role
    if (requiredRole && requiredRole !== activeRole) {
      if (window.$toast) window.$toast('身份不匹配，正在返回登录页...')
      localStorage.clear()
      setTimeout(() => { window.location.href = '/login' }, 1000)
      return
    }
  }

  next()
})

export default router