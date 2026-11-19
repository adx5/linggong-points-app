<!-- frontend/src/views/provider/ProviderSettings.vue —— 服务商端「设置」 -->
<template>
  <div class="pst-page">
    <section class="pst-group">
      <div class="pst-row">
        <span>消息通知</span>
        <button :class="['pst-switch', { on: notifyOn }]" @click="toggleNotify"><i></i></button>
      </div>
      <button class="pst-row" @click="openInfo('隐私设置')">
        <span>隐私设置</span><span class="pst-arrow">›</span>
      </button>
      <button class="pst-row" @click="openInfo('账号安全')">
        <span>账号安全</span><span class="pst-arrow">›</span>
      </button>
      <button class="pst-row" @click="openInfo('关于我们')">
        <span>关于我们</span><span class="pst-arrow">›</span>
      </button>
    </section>

    <!-- 信息弹层 -->
    <div v-if="infoOpen" class="pst-mask" @click.self="infoOpen = false">
      <div class="pst-sheet">
        <div class="pst-sheet-head">
          <h3>{{ infoTitle }}</h3>
          <span class="pst-sheet-close" @click="infoOpen = false">✕</span>
        </div>
        <p class="pst-sheet-body">{{ infoBody }}</p>
        <button class="pst-btn" @click="infoOpen = false">我知道了</button>
      </div>
    </div>

    <section class="pst-group">
      <div class="pst-row plain">
        <span>当前版本</span>
        <span class="pst-value">v0.1.0（Staging）</span>
      </div>
      <div class="pst-row plain">
        <span>所在城市</span>
        <span class="pst-value">{{ cityName }}</span>
      </div>
    </section>

    <button class="pst-logout" @click="logout">退出登录</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const notifyOn = ref(localStorage.getItem('provider_notify') !== '0')

const infoOpen = ref(false)
const infoTitle = ref('')
const infoBody = ref('')

const INFO = {
  隐私设置:
    '我们仅在您接单履约所必需的范围内使用您的资料：姓名、手机号与区镇用于客户联系与匹配；'
    + '不会向第三方出售。您可在「资质与实名认证」中更新资料，如需注销账号请联系平台客服。',
  账号安全:
    '· 请勿将登录手机号借给他人使用\n'
    + '· 平台不会以任何理由索要短信验证码\n'
    + '· 涉及改绑收款账户时，平台会二次核验身份\n'
    + '· 发现异常请立即联系客服冻结账号',
  关于我们:
    '零工小市场 · 服务商端\n'
    + '同城零工撮合与本地生活服务平台\n'
    + '平台仅提供信息撮合，不代收代付客户款项；服务费用由您与客户自行结算。'
}

function openInfo(name) {
  infoTitle.value = name
  infoBody.value = INFO[name] || ''
  infoOpen.value = true
}

const cityMap = { 410185: '登封', 410173: '航空港', 411300: '南阳' }
const cityName = cityMap[localStorage.getItem('guest_city_id') || '410185'] || '登封'

function toggleNotify() {
  notifyOn.value = !notifyOn.value
  localStorage.setItem('provider_notify', notifyOn.value ? '1' : '0')
  window.$toast && window.$toast(notifyOn.value ? '已开启消息通知' : '已关闭消息通知')
}

function todo(name) {
  openInfo(name)
}

function logout() {
  localStorage.clear()
  window.location.hash = '#/login'
  window.location.reload()
}
</script>

<style scoped>
.pst-page { min-height: 100vh; background: var(--bg); padding: 16px 20px 40px; }

.pst-group {
  background: #fff;
  border-radius: 16px;
  padding: 0 20px;
  margin-bottom: 18px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}
.pst-row {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 0;
  border: none;
  border-bottom: 1px solid #f0f2f5;
  background: none;
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  text-align: left;
}
.pst-row:last-child { border-bottom: none; }
.pst-row.plain { cursor: default; }
.pst-arrow { color: #c4ccd6; font-size: 18px; }
.pst-value { font-size: 14px; font-weight: 500; color: #7b8797; }

.pst-switch {
  width: 46px;
  height: 26px;
  border-radius: 999px;
  border: none;
  background: #dfe3ea;
  position: relative;
  transition: background 0.2s;
}
.pst-switch i {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  transition: left 0.2s;
}
.pst-switch.on { background: var(--g); }
.pst-switch.on i { left: 23px; }

.pst-logout {
  width: 100%;
  height: 52px;
  border-radius: 12px;
  background: #fff;
  color: var(--danger);
  border: 1px solid var(--line);
  font-size: 16px;
  font-weight: 800;
}

/* 信息弹层 */
.pst-mask { position: fixed; inset: 0; background: rgba(0,0,0,.42); z-index: 200; display: flex; align-items: flex-end; }
.pst-sheet { width: 100%; background: #fff; border-radius: 20px 20px 0 0; padding: 20px 20px 26px; max-height: 76vh; overflow-y: auto; }
.pst-sheet-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.pst-sheet-head h3 { font-size: 20px; font-weight: 800; color: var(--text); }
.pst-sheet-close { font-size: 18px; color: #9aa6b5; padding: 4px; }
.pst-sheet-body { font-size: 15px; color: #4a5565; line-height: 1.85; white-space: pre-wrap; }
.pst-btn {
  margin-top: 20px;
  width: 100%;
  height: 50px;
  border-radius: 12px;
  border: none;
  background: var(--g);
  color: #fff;
  font-size: 16px;
  font-weight: 800;
}
</style>
