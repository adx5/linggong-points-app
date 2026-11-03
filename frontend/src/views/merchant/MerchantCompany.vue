<!-- (企业管理中转页) -->
<template>
  <div class="company-page">
    <div class="sticky-header">
      <div class="header-left">
        <div class="btn-back" @click="$router.back()">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#1f2937" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
        </div>
        <h2>企业信息</h2>
      </div>
    </div>

    <div class="content">
      <!-- 🚨 1. 基本信息维护 -->
      <div class="menu-card" @click="$router.push('/merchant/info')">
        <div class="icon" style="background:#fce7f3; color:#ec4899;">🏢</div>
        <div class="info">
          <h3>基本信息维护</h3>
        </div>
        <div class="arrow">></div>
      </div>

      <!-- 🚨 2. 企业用工备案 -->
      <div class="menu-card" @click="$router.push('/merchant/verify')">
        <div class="icon" style="background:#dcfce7; color:#10b981;">🛡️</div>
        <div class="info">
          <h3>企业用工备案</h3>
        </div>
        <div class="arrow">></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.company-page { min-height: 100vh; background: #f0f2f5; }
.sticky-header { position: sticky; top: 0; z-index: 99; background: #fff; padding: 16px; border-bottom: 1px solid #eee; }
.header-left { display: flex; align-items: center; gap: 8px; }
.btn-back { cursor: pointer; display: flex; align-items: center; margin-left: -8px; }
.sticky-header h2 { font-size: 18px; color: #1f2937; }
.content { padding: 16px; }
.menu-card { display: flex; align-items: center; background: #fff; padding: 20px 16px; border-radius: 12px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); cursor: pointer; }
.icon { width: 48px; height: 48px; border-radius: 12px; display: flex; justify-content: center; align-items: center; font-size: 24px; margin-right: 16px; }
.info { flex: 1; display: flex; align-items: center; }
.info h3 { font-size: 16px; color: #333; margin: 0; font-weight: bold; }
.arrow { color: #ccc; font-size: 18px; }
</style>