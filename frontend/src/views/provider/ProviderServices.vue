<!-- frontend/src/views/provider/ProviderServices.vue —— 服务商端「服务管理」
     三个 tab：服务管理（我上架的服务）/ 咨询中（待接单）/ 服务中（已接单待完工）
-->
<template>
  <div class="ps-page">
    <div class="ps-tabs">
      <button
        v-for="t in tabs"
        :key="t.key"
        :class="['ps-tab', { active: activeTab === t.key }]"
        @click="switchTab(t.key)"
      >
        {{ t.label }}
        <span v-if="t.key === 'pending' && pendingList.length" class="ps-badge">{{ pendingList.length }}</span>
      </button>
    </div>

    <div class="ps-content">
      <!-- 服务管理 -->
      <template v-if="activeTab === 'services'">
        <article v-for="s in services" :key="s.id" class="ps-card">
          <div class="ps-card-head">
            <h3 class="ps-card-title">{{ s.title }}</h3>
            <span :class="['ps-status', s.status === 'active' ? 'ok' : 'off']">
              {{ s.status === 'active' ? '已上架' : '已下架' }}
            </span>
          </div>
          <div class="ps-price">￥{{ s.price }}<small>/{{ s.price_unit }}</small></div>
          <p class="ps-desc">{{ s.description || '暂无描述' }}</p>
          <div class="ps-ops">
            <button class="ps-btn" @click="openEdit(s)">编辑服务</button>
            <button class="ps-btn" @click="toggle(s)">{{ s.status === 'active' ? '下架服务' : '重新上架' }}</button>
          </div>
        </article>

        <button class="ps-publish" @click="goPublish">
          <span class="ps-plus">+</span>
          <span>发布新服务</span>
        </button>

        <p v-if="!services.length && !loading" class="ps-tip">还没有上架的服务，点上方按钮发布第一条</p>
      </template>

      <!-- 咨询中 -->
      <template v-else-if="activeTab === 'pending'">
        <article v-for="o in pendingList" :key="o.id" class="ps-order pending">
          <div class="ps-card-head">
            <h3 class="ps-card-title">{{ o.title }}</h3>
            <span class="ps-status warn">待联系</span>
          </div>
          <div class="ps-order-info">
            <div><span>客户：</span>{{ o.contact_phone || '未留电话' }}</div>
            <div><span>时间：</span>{{ o.scheduled_at || o.created_at }}</div>
            <div v-if="o.address"><span>地址：</span>{{ o.address }}</div>
          </div>
          <div class="ps-order-ops">
            <a v-if="o.contact_phone" class="ps-call" :href="`tel:${o.contact_phone}`">📞 拨打客户电话</a>
            <button class="ps-accept" @click="accept(o)">接单</button>
          </div>
        </article>
        <p v-if="!pendingList.length && !loading" class="ps-tip">暂无待联系的咨询</p>
      </template>

      <!-- 服务中 -->
      <template v-else>
        <article v-for="o in activeList" :key="o.id" class="ps-order doing">
          <div class="ps-card-head">
            <h3 class="ps-card-title">{{ o.title }}</h3>
            <span class="ps-status ok">服务中</span>
          </div>
          <div class="ps-order-info">
            <div><span>客户：</span>{{ o.contact_phone || '未留电话' }}</div>
            <div><span>预约：</span>{{ o.scheduled_at || o.created_at }}</div>
            <div v-if="o.address"><span>地址：</span>{{ o.address }}</div>
          </div>
          <div class="ps-order-ops">
            <a v-if="o.contact_phone" class="ps-call ghost" :href="`tel:${o.contact_phone}`">📞 联系客户</a>
            <button class="ps-accept" @click="finish(o)">完工报备</button>
          </div>
        </article>
        <p v-if="!activeList.length && !loading" class="ps-tip">暂无进行中的服务</p>
      </template>
    </div>

    <!-- 编辑服务弹窗 -->
    <div v-if="editOpen" class="ps-mask" @click.self="editOpen = false">
      <div class="ps-sheet">
        <div class="ps-sheet-head">
          <h3>编辑服务</h3>
          <span class="ps-sheet-close" @click="editOpen = false">✕</span>
        </div>

        <label class="ps-field">
          <span>服务名称</span>
          <input v-model="editForm.title" maxlength="40" placeholder="例如：深度保洁 · 全屋大扫除" />
        </label>

        <div class="ps-field-row">
          <label class="ps-field">
            <span>价格（元）</span>
            <input v-model.number="editForm.price" type="number" min="0" placeholder="0" />
          </label>
          <label class="ps-field">
            <span>计价单位</span>
            <select v-model="editForm.price_unit">
              <option value="次">次</option>
              <option value="小时">小时</option>
              <option value="天">天</option>
              <option value="平方米">平方米</option>
            </select>
          </label>
        </div>

        <label class="ps-field">
          <span>服务说明</span>
          <textarea v-model="editForm.description" rows="3" maxlength="200" placeholder="包含哪些内容、服务范围等"></textarea>
        </label>

        <div class="ps-sheet-actions">
          <button class="ps-btn" @click="editOpen = false">取消</button>
          <button class="ps-accept" :disabled="saving" @click="saveEdit">{{ saving ? '保存中…' : '保存' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()

const tabs = [
  { key: 'services', label: '服务管理' },
  { key: 'pending', label: '咨询中' },
  { key: 'accepted', label: '服务中' }
]
const activeTab = ref('services')

const services = ref([])
const pendingList = ref([])
const activeList = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    if (activeTab.value === 'services') {
      const res = await api.get('/services/my-services')
      services.value = res.data || []
    } else {
      const status = activeTab.value === 'pending' ? 'pending' : 'accepted'
      const res = await api.get('/services/orders/provider', { params: { status } })
      if (activeTab.value === 'pending') pendingList.value = res.data || []
      else activeList.value = res.data || []
    }
  } catch (err) {
    if (window.$toast) window.$toast(err.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

function switchTab(key) {
  activeTab.value = key
  load()
}

function goPublish() {
  router.push('/provider/publish')
}

// 编辑服务
const editOpen = ref(false)
const saving = ref(false)
const editTarget = ref(null)
const editForm = ref({ title: '', price: 0, price_unit: '次', description: '' })

function openEdit(s) {
  editTarget.value = s
  editForm.value = {
    title: s.title || '',
    price: s.price || 0,
    price_unit: s.price_unit || '次',
    description: s.description || ''
  }
  editOpen.value = true
}

async function saveEdit() {
  if (!String(editForm.value.title || '').trim()) {
    return window.$toast && window.$toast('请填写服务名称')
  }
  saving.value = true
  try {
    const res = await api.put(`/services/my-services/${editTarget.value.id}`, {
      title: editForm.value.title,
      price: Number(editForm.value.price) || 0,
      price_unit: editForm.value.price_unit,
      description: editForm.value.description
    })
    Object.assign(editTarget.value, res.data || {})
    editOpen.value = false
    window.$toast && window.$toast('服务信息已更新')
  } catch (err) {
    window.$toast && window.$toast(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function toggle(s) {
  const next = s.status === 'active' ? 'off' : 'active'
  try {
    await api.put(`/services/my-services/${s.id}/status`, null, { params: { status: next } })
    s.status = next
    window.$toast && window.$toast(next === 'active' ? '已上架' : '已下架')
  } catch (err) {
    window.$toast && window.$toast(err.response?.data?.detail || '操作失败')
  }
}

async function accept(o) {
  try {
    await api.put(`/services/orders/${o.id}/accept`)
    window.$toast && window.$toast('已接单，请按时上门')
    switchTab('accepted')
  } catch (err) {
    window.$toast && window.$toast(err.response?.data?.detail || '接单失败')
  }
}

async function finish(o) {
  try {
    await api.put(`/services/orders/${o.id}/finish`)
    window.$toast && window.$toast('已完工报备')
    load()
  } catch (err) {
    window.$toast && window.$toast(err.response?.data?.detail || '操作失败')
  }
}

onMounted(load)
</script>

<style scoped>
.ps-page { min-height: 100vh; background: var(--bg); }

.ps-tabs {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  background: #fff;
  border-bottom: 1px solid #eef0f3;
}
.ps-tab {
  flex: 1;
  position: relative;
  padding: 16px 0;
  border: none;
  background: none;
  font-size: 16px;
  color: #666;
}
.ps-tab.active { color: var(--text); font-weight: 800; }
.ps-tab.active::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 0;
  transform: translateX(-50%);
  width: 24px;
  height: 3px;
  border-radius: 2px;
  background: var(--g);
}
.ps-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  margin-left: 4px;
  padding: 0 4px;
  border-radius: 9px;
  background: var(--danger);
  color: #fff;
  font-size: 11px;
  font-weight: 800;
}

.ps-content { padding: 16px 20px 90px; }

.ps-card, .ps-order {
  background: #fff;
  border-radius: 16px;
  padding: 18px 20px;
  margin-bottom: 14px;
  border: 1px solid var(--line);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}
.ps-order.pending { border-left: 4px solid #ffd700; }
.ps-order.doing { border-left: 4px solid var(--g); }

.ps-card-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 10px; }
.ps-card-title { font-size: 18px; font-weight: 800; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ps-status { flex-shrink: 0; font-size: 13px; font-weight: 700; padding: 4px 8px; border-radius: 4px; }
.ps-status.ok { color: var(--g-text); background: var(--g-soft); }
.ps-status.off { color: #8b95a5; background: #f2f4f7; }
.ps-status.warn { color: var(--warn); background: var(--warn-soft); }

.ps-price { font-size: 20px; font-weight: 800; color: #ff6b00; margin-bottom: 10px; }
.ps-price small { font-size: 14px; }
.ps-desc { font-size: 14px; color: #666; line-height: 1.6; margin-bottom: 16px; }

.ps-ops { display: flex; gap: 12px; }
.ps-btn {
  flex: 1;
  height: 40px;
  border-radius: 8px;
  border: 1px solid #ddd;
  background: #fff;
  color: #555;
  font-size: 15px;
  font-weight: 700;
}

.ps-publish {
  margin-top: 24px;
  width: 100%;
  height: 140px;
  border-radius: 16px;
  border: 2px dashed var(--g);
  background: #f9fafc;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--g-text);
  font-size: 18px;
  font-weight: 800;
}
.ps-plus { font-size: 32px; line-height: 1; color: var(--g); }

.ps-order-info {
  background: #f9fafc;
  border-radius: 10px;
  padding: 12px;
  font-size: 15px;
  color: #333;
  line-height: 1.8;
  margin-bottom: 14px;
}
.ps-order-info span { color: #999; }

.ps-order-ops { display: flex; gap: 12px; }
.ps-call {
  flex: 1;
  height: 52px;
  border-radius: 12px;
  background: var(--g);
  color: #fff;
  font-size: 17px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
}
.ps-call.ghost { background: var(--bg); color: #555; }
.ps-accept {
  flex: 1;
  height: 52px;
  border-radius: 12px;
  border: none;
  background: var(--g);
  color: #fff;
  font-size: 17px;
  font-weight: 800;
}

.ps-tip { text-align: center; font-size: 14px; color: #9aa6b5; padding: 24px 0; }

/* 编辑服务弹窗 */
.ps-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.42);
  z-index: 200;
  display: flex;
  align-items: flex-end;
}
.ps-sheet {
  width: 100%;
  background: #fff;
  border-radius: 20px 20px 0 0;
  padding: 20px 20px 26px;
  max-height: 86vh;
  overflow-y: auto;
}
.ps-sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.ps-sheet-head h3 { font-size: 20px; font-weight: 800; color: var(--text); }
.ps-sheet-close { font-size: 18px; color: #9aa6b5; padding: 4px; }

.ps-field { display: block; margin-bottom: 14px; flex: 1; }
.ps-field > span { display: block; font-size: 13px; color: #7b8797; margin-bottom: 6px; font-weight: 600; }
.ps-field input,
.ps-field select,
.ps-field textarea {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #f9fafc;
  padding: 13px 14px;
  font-size: 16px;
  color: var(--text);
  outline: none;
  font-family: inherit;
}
.ps-field input:focus,
.ps-field select:focus,
.ps-field textarea:focus { border-color: var(--g); background: #fff; }
.ps-field textarea { resize: none; line-height: 1.6; }
.ps-field-row { display: flex; gap: 12px; }

.ps-sheet-actions { display: flex; gap: 12px; margin-top: 8px; }
.ps-sheet-actions .ps-btn { flex: 1; height: 50px; }
.ps-sheet-actions .ps-accept { flex: 2; }
.ps-accept:disabled { opacity: 0.6; }
</style>
