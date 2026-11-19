<!-- frontend/src/views/provider/ProviderHomepage.vue —— 我的主页展示（预览 + 展示开关） -->
<template>
  <div class="ph2-page">
    <p class="ph2-label">客户看到的预览效果</p>

    <section class="ph2-preview">
      <div class="ph2-cover"></div>
      <div class="ph2-body">
        <div class="ph2-avatar">{{ (profile.display_name || '服')[0] }}</div>
        <h2 class="ph2-name">{{ profile.display_name || '未设置名称' }}</h2>
        <p class="ph2-sub">
          {{ profile.verify_status === 'verified' ? '已实名认证' : '未实名' }}
          · {{ profile.category_name }} · {{ profile.district || '登封' }}
        </p>

        <div class="ph2-tags">
          <span v-for="t in tags" :key="t" class="ph2-tag">{{ t }}</span>
          <span v-if="!tags.length" class="ph2-tag">暂无服务标签</span>
        </div>

        <div class="ph2-stats">
          <span v-if="showOrders">累计接单 {{ profile.orders_done }} 单</span>
          <span v-if="showRating">好评率 {{ goodRate }}%</span>
          <span v-if="!showOrders && !showRating" class="ph2-muted">已隐藏接单数与好评率</span>
        </div>
      </div>
    </section>

    <p class="ph2-label">展示设置</p>
    <section class="ph2-group">
      <div class="ph2-row">
        <span>展示接单数量</span>
        <button :class="['ph2-switch', { on: showOrders }]" @click="toggle('orders')"><i></i></button>
      </div>
      <div class="ph2-row">
        <span>展示客户好评率</span>
        <button :class="['ph2-switch', { on: showRating }]" @click="toggle('rating')"><i></i></button>
      </div>
    </section>

    <p class="ph2-hint">设置会实时反映到上方预览，客户看到的即为预览效果。</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api'

const profile = ref({})
const tags = ref([])
const goodRate = ref(100)

const showOrders = ref(localStorage.getItem('provider_show_orders') !== '0')
const showRating = ref(localStorage.getItem('provider_show_rating') !== '0')

const tagsComputed = computed(() => tags.value)

function toggle(kind) {
  if (kind === 'orders') {
    showOrders.value = !showOrders.value
    localStorage.setItem('provider_show_orders', showOrders.value ? '1' : '0')
  } else {
    showRating.value = !showRating.value
    localStorage.setItem('provider_show_rating', showRating.value ? '1' : '0')
  }
}

async function load() {
  try {
    const res = await api.get('/services/my-profile')
    profile.value = res.data || {}
    tags.value = (res.data?.tags || []).slice(0, 6)
  } catch (err) {
    profile.value = {}
  }

  try {
    const d = await api.get(`/services/providers/${profile.value.id}`)
    goodRate.value = d.data?.stats?.good_rate ?? 100
  } catch (err) {}
}

onMounted(load)
</script>

<style scoped>
.ph2-page { min-height: 100vh; background: var(--bg); padding: 16px 20px 40px; }
.ph2-label { font-size: 15px; font-weight: 800; color: #333; margin: 4px 0 12px 4px; }

.ph2-preview {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 22px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}
.ph2-cover { height: 100px; background: linear-gradient(135deg, var(--g), #00e676); }
.ph2-body { padding: 0 20px 20px; margin-top: -30px; }
.ph2-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--g-soft);
  border: 3px solid #fff;
  color: var(--g-text);
  font-size: 26px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}
.ph2-name { font-size: 20px; font-weight: 800; color: var(--text); margin-bottom: 6px; }
.ph2-sub { font-size: 14px; color: #666; margin-bottom: 14px; }

.ph2-tags { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; }
.ph2-tag {
  background: var(--g-soft);
  color: var(--g-text);
  font-size: 13px;
  font-weight: 800;
  padding: 4px 10px;
  border-radius: 4px;
}

.ph2-stats { display: flex; gap: 16px; font-size: 13px; color: #7b8797; }
.ph2-muted { color: #b9c2cc; }

.ph2-group {
  background: #fff;
  border-radius: 16px;
  padding: 0 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}
.ph2-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 0;
  border-bottom: 1px solid #f0f2f5;
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
}
.ph2-row:last-child { border-bottom: none; }

.ph2-switch {
  width: 46px;
  height: 26px;
  border-radius: 999px;
  border: none;
  background: #dfe3ea;
  position: relative;
  transition: background 0.2s;
}
.ph2-switch i {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  transition: left 0.2s;
}
.ph2-switch.on { background: var(--g); }
.ph2-switch.on i { left: 23px; }

.ph2-hint { font-size: 13px; color: #9aa6b5; margin-top: 14px; padding-left: 4px; line-height: 1.6; }
</style>
