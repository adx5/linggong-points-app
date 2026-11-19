<!-- frontend/src/views/merchant/MerchantSettings.vue (B端设置中心：可点开、内容真实) -->
<template>
  <div class="settings-page">
    <div class="sticky-header">
      <h2>设置中心</h2>
    </div>

    <div class="menu-list">
      <div class="menu-item" @click="openInfo('账号安全')">
        <span>账号安全</span>
        <span class="arrow">></span>
      </div>
      <div class="menu-item" @click="openInfo('发票管理')">
        <span>发票管理</span>
        <span class="arrow">></span>
      </div>
      <div class="menu-item" @click="callService">
        <span>联系平台客服</span>
        <span class="arrow">></span>
      </div>
      <div class="menu-item" @click="openInfo('关于平台')">
        <span>关于平台</span>
        <span class="version">v1.0.0</span>
      </div>
    </div>

    <div class="action-area">
      <span class="btn-logout-text" @click="logout">退出登录 / 切换身份</span>
    </div>

    <!-- 信息弹层 -->
    <div v-if="infoOpen" class="mask" @click.self="infoOpen = false">
      <div class="sheet">
        <div class="sheet-head">
          <h3>{{ infoTitle }}</h3>
          <span class="sheet-close" @click="infoOpen = false">✕</span>
        </div>
        <p class="sheet-body">{{ infoBody }}</p>
        <button class="sheet-btn" @click="infoOpen = false">我知道了</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const infoOpen = ref(false)
const infoTitle = ref('')
const infoBody = ref('')

const INFO = {
  账号安全:
    '· 企业账号与法人手机号绑定，请勿转借他人\n'
    + '· 平台不会以任何理由索要短信验证码\n'
    + '· 修改收款账户时平台会二次核验身份\n'
    + '· 发现异常请立即联系客服冻结账号',
  发票管理:
    '推广积分充值、加热置顶等费用可按月开票。\n'
    + '请在充值成功后联系平台运营提供：企业全称、纳税人识别号、开票金额与接收邮箱。\n'
    + '发票为增值税普通发票，一般 5 个工作日内开具。',
  关于平台:
    '零工小市场 · 企业端 v1.0.0\n'
    + '同城零工撮合与本地生活服务平台。\n'
    + '平台仅提供信息撮合服务，不代收代付求职者款项；工资由企业与员工自行结算。\n'
    + '推广积分仅用于平台内曝光与激励，不可提现。'
}

function openInfo(name) {
  infoTitle.value = name
  infoBody.value = INFO[name] || ''
  infoOpen.value = true
}

function callService() {
  window.location.href = 'tel:4000000000'
}

const logout = () => {
  localStorage.clear()
  window.location.hash = '#/login'
  window.location.reload()
}
</script>

<style scoped>
.settings-page { min-height: 100vh; background: #f0f2f5; display: flex; flex-direction: column; }
.sticky-header { position: sticky; top: 0; z-index: 99; background: #fff; padding: 16px; border-bottom: 1px solid #eee; }
.sticky-header h2 { font-size: 18px; color: #1f2937; }
.menu-list { background: #fff; margin: 16px; border-radius: 12px; padding: 0 16px; }
.menu-item { display: flex; justify-content: space-between; padding: 18px 0; border-bottom: 1px solid #f3f4f6; font-size: 15px; color: #333; cursor: pointer; }
.menu-item:last-child { border-bottom: none; }
.menu-item:active { background: #f9fafb; }
.arrow { color: #ccc; }
.version { font-size: 14px; color: #9ca3af; }
.action-area { display: flex; justify-content: center; margin-top: auto; padding: 20px 0; }
.btn-logout-text { font-size: 13px; color: #94a3b8; padding: 8px 20px; cursor: pointer; }
.btn-logout-text:active { color: #64748b; }

/* 信息弹层 */
.mask { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.42); z-index: 200; display: flex; align-items: flex-end; }
.sheet { width: 100%; background: #fff; border-radius: 20px 20px 0 0; padding: 20px 20px 26px; max-height: 76vh; overflow-y: auto; }
.sheet-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.sheet-head h3 { font-size: 20px; font-weight: 800; color: #111; }
.sheet-close { font-size: 18px; color: #9aa6b5; padding: 4px; }
.sheet-body { font-size: 15px; color: #4a5565; line-height: 1.85; white-space: pre-wrap; }
.sheet-btn { margin-top: 20px; width: 100%; height: 50px; border-radius: 12px; border: none; background: #2563eb; color: #fff; font-size: 16px; font-weight: 800; }
</style>
