<!-- (Gov监管大屏：只读大屏，绝不越权操作) -->
<template>
  <div class="gov-page">
    <div class="header">
      <h2>政务监管数据大屏</h2>
      <p>脱敏数据 · 只读镜像 · 政务专网</p>
    </div>

    <div class="read-only-banner">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px; margin-top:-2px;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
      当前为政务专网镜像数据，不可在此处操作
    </div>

    <div class="dashboard-content">
      <!-- 第一区 -->
      <div class="block-section">
        <div class="block-title"><span class="line red"></span> 劳动监察 (维权与惩戒)</div>
        <div class="block-cards">
          <div class="grid-item">
            <div class="icon-wrap red-icon"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v18"></path><path d="M8 21h8"></path><path d="M3 7l4-4 4 4"></path><path d="M17 7l4-4 4 4"></path><path d="M3 7v6a4 4 0 0 0 8 0V7"></path><path d="M17 7v6a4 4 0 0 0 8 0V7"></path></svg></div>
            <span class="name">纠纷调解</span><span class="val text-red">{{ govData.disputes }} 件</span>
          </div>
          <div class="grid-item">
            <div class="icon-wrap red-icon"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line></svg></div>
            <span class="name">黑名单惩戒</span><span class="val text-red">{{ govData.blacklist }} 家</span>
          </div>
          <div class="grid-item">
            <div class="icon-wrap red-icon"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg></div>
            <span class="name">企业信用库</span><span class="val text-green">正常</span>
          </div>
        </div>
      </div>

      <!-- 第二区 -->
      <div class="block-section">
        <div class="block-title"><span class="line blue"></span> 工商与资质核查 (穿透监管)</div>
        <div class="block-cards">
          <div class="grid-item">
            <div class="icon-wrap blue-icon"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg></div>
            <span class="name">红盾比对</span><span class="val text-blue">已同步</span>
          </div>
          <div class="grid-item">
            <div class="icon-wrap blue-icon"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg></div>
            <span class="name">经纪人核查</span><span class="val text-blue">已同步</span>
          </div>
          <div class="grid-item">
            <div class="icon-wrap blue-icon"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg></div>
            <span class="name">空壳预警</span><span class="val text-red">{{ govData.shell_companies }} 家</span>
          </div>
        </div>
      </div>

      <!-- 第三区 -->
      <div class="block-section">
        <div class="block-title"><span class="line green"></span> 宏观数据 (脱敏看板)</div>
        <div class="block-cards">
          <div class="grid-item">
            <div class="icon-wrap green-icon"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg></div>
            <span class="name">就业大屏</span><span class="val text-green">只读</span>
          </div>
          <div class="grid-item">
            <div class="icon-wrap green-icon"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20"></path><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg></div>
            <span class="name">薪资分布</span><span class="val text-green">只读</span>
          </div>
          <div class="grid-item">
            <div class="icon-wrap green-icon"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg></div>
            <span class="name">政策发布</span><span class="val text-blue">最新</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const govData = ref({ disputes: 0, blacklist: 0, shell_companies: 0 })

onMounted(async () => {
  try {
    // 🚨 核心：路径必须是相对 /api 的 /audit/gov-dashboard
    const res = await api.get('/audit/gov-dashboard')
    govData.value = res.data
  } catch (err) {
    console.error('获取大屏数据失败:', err)
  }
})
</script>

<style scoped>
.gov-page { min-height: 100vh; background: #f0f4f8; padding-bottom: 80px; }
.header { background: #0052d9; padding: 30px 20px 20px; color: #ffffff; }
.header h2 { font-size: 20px; margin-bottom: 4px; }
.header p { font-size: 13px; opacity: 0.8; }
.read-only-banner { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; padding: 10px; text-align: center; font-size: 13px; font-weight: bold; margin: 16px; border-radius: 8px; }
.dashboard-content { padding: 0 16px; display: flex; flex-direction: column; gap: 16px; }
.block-section { background: #ffffff; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
.block-title { font-size: 15px; font-weight: bold; color: #1f2937; margin-bottom: 16px; display: flex; align-items: center; }
.block-title .line { display: inline-block; width: 4px; height: 14px; border-radius: 2px; margin-right: 8px; }
.line.red { background: #ef4444; }
.line.blue { background: #0052d9; }
.line.green { background: #10b981; }
.block-cards { display: flex; justify-content: space-between; gap: 10px; }
.grid-item { flex: 1; display: flex; flex-direction: column; align-items: center; padding: 12px 4px; border-radius: 8px; background: #f9fafb; border: 1px solid #f3f4f6; }
.icon-wrap { width: 40px; height: 40px; border-radius: 10px; display: flex; justify-content: center; align-items: center; margin-bottom: 8px; }
.red-icon { background: #fef2f2; color: #ef4444; }
.blue-icon { background: #eff6ff; color: #0052d9; }
.green-icon { background: #ecfdf5; color: #10b981; }
.name { font-size: 12px; color: #333333; font-weight: bold; text-align: center; margin-bottom: 4px; white-space: nowrap; }
.val { font-size: 11px; font-weight: bold; }
.text-red { color: #ef4444; }
.text-green { color: #10b981; }
.text-blue { color: #0052d9; }
</style>