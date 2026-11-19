<!-- frontend/src/views/provider/ProviderPublish.vue —— B 端「一键直发」5 步向导
     1 选类目 → 2 选服务项 → 3 从业经验/门店 → 4 服务优势 → 5 确认名片与起步价
     提交调用 POST /api/services/my-services
-->
<template>
  <div class="pp-page">
    <header class="pp-header">
      <button class="pp-back" @click="onBack">{{ step === 1 ? '✕' : '←' }}</button>
      <span class="pp-title">{{ titles[step - 1] }}</span>
      <span class="pp-step">{{ step }}/5</span>
    </header>

    <div class="pp-progress">
      <span v-for="n in 5" :key="n" :class="['pp-dot', { on: n <= step }]"></span>
    </div>

    <div class="pp-content">
      <!-- Step 1 类目 -->
      <template v-if="step === 1">
        <h2 class="pp-h2">您擅长做什么？</h2>
        <p class="pp-sub">只需点选，平台自动帮您写介绍。</p>
        <div class="pp-grid2">
          <button
            v-for="c in categories"
            :key="c.id"
            :class="['pp-card', { on: categoryId === c.id }]"
            @click="pickCategory(c)"
          >
            <span class="pp-emoji">{{ c.icon || '🛠️' }}</span>
            <span>{{ c.name }}</span>
            <span v-if="categoryId === c.id" class="pp-check">✓</span>
          </button>
        </div>
      </template>

      <!-- Step 2 服务项 -->
      <template v-else-if="step === 2">
        <h2 class="pp-h2">具体能做哪些？</h2>
        <p class="pp-sub">可多选，选得越准，接单越快。</p>
        <div class="pp-pills">
          <button
            v-for="item in subItemOptions"
            :key="item"
            :class="['pp-pill', { on: subItems.includes(item) }]"
            @click="toggleItem(item)"
          >
            {{ item }}
            <span v-if="subItems.includes(item)" class="pp-check">✓</span>
          </button>
        </div>
      </template>

      <!-- Step 3 经验 + 门店 -->
      <template v-else-if="step === 3">
        <h2 class="pp-h2">您干这行多久了？</h2>
        <p class="pp-sub">经验越丰富，客户越信任。</p>
        <button
          v-for="e in experiences"
          :key="e"
          :class="['pp-opt', { on: experience === e }]"
          @click="experience = e"
        >
          {{ e }}<span v-if="experience === e" class="pp-check">✓</span>
        </button>

        <h2 class="pp-h2 mt">有实体门店吗？</h2>
        <div class="pp-row2">
          <button
            v-for="s in storeOptions"
            :key="s"
            :class="['pp-opt small', { on: hasStore === s }]"
            @click="hasStore = s"
          >
            {{ s }}<span v-if="hasStore === s" class="pp-check">✓</span>
          </button>
        </div>
      </template>

      <!-- Step 4 服务优势 -->
      <template v-else-if="step === 4">
        <h2 class="pp-h2">选几个您的服务优势</h2>
        <p class="pp-sub">最多选 3 个（已选 {{ advantages.length }}/3）</p>
        <div class="pp-pills">
          <button
            v-for="a in advantageOptions"
            :key="a"
            :class="['pp-pill', { on: advantages.includes(a) }]"
            @click="toggleAdvantage(a)"
          >
            {{ a }}<span v-if="advantages.includes(a)" class="pp-check">✓</span>
          </button>
        </div>
      </template>

      <!-- Step 5 确认 -->
      <template v-else>
        <h2 class="pp-h2">已为您生成名片</h2>
        <p class="pp-sub">选一个您喜欢的介绍方式：</p>

        <button
          v-for="card in cards"
          :key="card.key"
          :class="['pp-card-text', { on: cardStyle === card.key }]"
          @click="cardStyle = card.key"
        >
          <span class="pp-card-label">{{ card.key === 'A' ? '方案 A（踏实靠谱型）' : '方案 B（专业推荐型）' }}</span>
          <span class="pp-card-body">{{ card.text }}</span>
          <span class="pp-card-check">{{ cardStyle === card.key ? '✓' : '○' }}</span>
        </button>

        <h2 class="pp-h2 mt">设置起步价</h2>
        <div class="pp-price-box">
          <span class="pp-yen">￥</span>
          <input v-model.number="price" type="number" min="0" class="pp-price-input" />
          <select v-model="priceUnit" class="pp-unit">
            <option value="小时">元/小时</option>
            <option value="次">元/次</option>
            <option value="天">元/天</option>
            <option value="平方米">元/平方米</option>
          </select>
        </div>
      </template>
    </div>

    <div class="pp-action">
      <p class="pp-tip">{{ tips[step - 1] }}</p>
      <button class="pp-next" :disabled="submitting" @click="next">
        {{ step === 5 ? (submitting ? '上架中…' : '立即上架，开始接单') : '下一步' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()

const titles = ['一键直发', '发布服务', '从业经验', '服务优势', '确认上架']
const tips = [
  '简单 5 步，轻松发布',
  '已完成第一步，继续',
  '快完成了，坚持一下',
  '最后一步，马上上架',
  '请确认以上信息，无误即可上架'
]

const step = ref(1)
const submitting = ref(false)

const categories = ref([])
const categoryId = ref(null)
const categoryName = ref('')

const subItems = ref([])
const experience = ref('')
const hasStore = ref('')
const advantages = ref([])
const cardStyle = ref('A')
const price = ref(50)
const priceUnit = ref('小时')

const experiences = ['新手（1年内）', '老手（3-5年）', '专家（5年以上）']
const storeOptions = ['个人接单', '有实体门店']
const advantageOptions = ['干活细致', '自带工具', '明码标价', '自带清洁剂', '已实名', '不满意重做']

// 各品类的具体服务项
const SUB_ITEMS = {
  家政保洁: ['日常保洁', '深度大扫除', '擦玻璃', '洗油烟机', '开荒保洁', '收纳整理', '洗地毯', '洗窗帘', '除甲醛', '除螨除菌'],
  维修安装: ['空调维修', '空调加氟', '热水器维修', '油烟机安装', '洗衣机维修', '冰箱维修'],
  搬家搬运: ['小型搬家', '家具拆装', '长途搬运', '钢琴搬运', '公司搬迁'],
  水电维修: ['水电改造', '漏水检测', '电路检修', '龙头更换', '马桶安装'],
  开锁换锁: ['开锁', '换锁芯', '配钥匙', '智能锁安装'],
  上门理发: ['老人理发', '儿童理发', '上门美发']
}

const subItemOptions = computed(() => SUB_ITEMS[categoryName.value] || ['标准服务', '上门服务', '加急服务'])

function yearText() {
  if (experience.value.includes('5年')) return '8'
  if (experience.value.includes('3-5')) return '5'
  return '1'
}

const cards = computed(() => {
  const items = subItems.value.slice(0, 2).join('、') || '各类服务'
  const adv = advantages.value.join('、') || '干活细致'
  const store = hasStore.value === '有实体门店' ? '有实体门店，' : ''

  return [
    {
      key: 'A',
      text: `从业${yearText()}年${categoryName.value || '本地服务'}老手，干活细致，自带专业工具。擅长${items}。${store}明码标价，欢迎来电。`
    },
    {
      key: 'B',
      text: `${yearText()}年资深${categoryName.value || '本地服务'}师傅，主打${items}。服务优势：${adv}。${store}接单时间灵活，价格公道。`
    }
  ]
})

async function loadCategories() {
  try {
    const res = await api.get('/services/categories')
    categories.value = res.data || []
  } catch (err) {
    categories.value = []
  }
}

function pickCategory(c) {
  categoryId.value = c.id
  categoryName.value = c.name
  subItems.value = []
}

function toggleItem(item) {
  const i = subItems.value.indexOf(item)
  if (i >= 0) subItems.value.splice(i, 1)
  else subItems.value.push(item)
}

function toggleAdvantage(a) {
  const i = advantages.value.indexOf(a)
  if (i >= 0) return advantages.value.splice(i, 1)
  if (advantages.value.length >= 3) return window.$toast && window.$toast('最多选 3 个优势')
  advantages.value.push(a)
}

function validate() {
  if (step.value === 1 && !categoryId.value) return '请先选择服务类目'
  if (step.value === 2 && !subItems.value.length) return '至少选择一个具体服务项'
  if (step.value === 3 && (!experience.value || !hasStore.value)) return '请选择从业经验和接单方式'
  if (step.value === 4 && !advantages.value.length) return '至少选择一个服务优势'
  if (step.value === 5 && (!price.value || Number(price.value) <= 0)) return '请填写有效的起步价'
  return ''
}

function onBack() {
  if (step.value === 1) return router.back()
  step.value -= 1
}

async function next() {
  const err = validate()
  if (err) return window.$toast && window.$toast(err)

  if (step.value < 5) {
    step.value += 1
    return
  }

  // 提交
  submitting.value = true
  try {
    const text = cards.value.find((c) => c.key === cardStyle.value)?.text || ''
    const title = subItems.value.length
      ? `${categoryName.value} · ${subItems.value[0]}`
      : categoryName.value

    await api.post('/services/my-services', {
      category_id: categoryId.value,
      title,
      price: Number(price.value),
      price_unit: priceUnit.value,
      description: text,
      meta: {
        sub_items: subItems.value,
        experience: experience.value,
        has_store: hasStore.value,
        advantages: advantages.value,
        card_style: cardStyle.value
      }
    })

    window.$toast && window.$toast('上架成功，开始接单吧')
    setTimeout(() => router.replace('/provider/services'), 700)
  } catch (e) {
    window.$toast && window.$toast(e.response?.data?.detail || '上架失败，请重试')
  } finally {
    submitting.value = false
  }
}

onMounted(loadCategories)
</script>

<style scoped>
.pp-page { min-height: 100vh; background: var(--bg); padding-bottom: 130px; }

.pp-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 12px;
  background: #fff;
  border-bottom: 1px solid #eef0f3;
}
.pp-back { border: none; background: none; font-size: 26px; line-height: 1; width: 44px; text-align: left; color: #333; padding-bottom: 4px; }
.pp-title { flex: 1; text-align: center; font-size: 18px; font-weight: 800; color: var(--text); }
.pp-step { width: 44px; text-align: right; font-size: 13px; color: #9aa6b5; }

.pp-progress { display: flex; gap: 6px; padding: 12px 20px 0; }
.pp-dot { flex: 1; height: 4px; border-radius: 2px; background: #e5e8ee; }
.pp-dot.on { background: var(--g); }

.pp-content { padding: 20px; }
.pp-h2 { font-size: 22px; font-weight: 800; color: var(--text); margin-bottom: 8px; }
.pp-h2.mt { margin-top: 28px; }
.pp-sub { font-size: 14px; color: #7b8797; margin-bottom: 18px; }

.pp-grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.pp-card {
  position: relative;
  height: 84px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 17px;
  font-weight: 800;
  color: #333;
}
.pp-emoji { font-size: 24px; }
.pp-card.on { border-color: var(--g); background: var(--g-soft); color: var(--g-text); }

.pp-check { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); color: var(--g); font-weight: 900; }

.pp-pills { display: flex; flex-wrap: wrap; gap: 12px; }
.pp-pill {
  position: relative;
  min-width: 45%;
  flex: 1 1 45%;
  height: 54px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: #fff;
  font-size: 16px;
  font-weight: 700;
  color: #333;
}
.pp-pill.on { border-color: var(--g); background: var(--g-soft); color: var(--g-text); }

.pp-opt {
  position: relative;
  width: 100%;
  height: 60px;
  margin-bottom: 12px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: #fff;
  font-size: 17px;
  font-weight: 700;
  color: #333;
  text-align: left;
  padding-left: 20px;
}
.pp-opt.on { border-color: var(--g); background: var(--g-soft); color: var(--g-text); }
.pp-opt.small { text-align: center; padding-left: 0; }
.pp-row2 { display: flex; gap: 12px; }
.pp-row2 .pp-opt { margin-bottom: 0; }

.pp-card-text {
  position: relative;
  display: block;
  width: 100%;
  text-align: left;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 12px;
}
.pp-card-text.on { border: 2px solid var(--g); background: var(--g-soft); }
.pp-card-label { display: block; font-size: 13px; font-weight: 800; color: #7b8797; margin-bottom: 8px; }
.pp-card-text.on .pp-card-label { color: var(--g-text); }
.pp-card-body { font-size: 15px; color: #333; line-height: 1.65; }
.pp-card-check { position: absolute; right: 16px; top: 16px; color: var(--g); font-size: 18px; font-weight: 900; }

.pp-price-box {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 6px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 22px;
}
.pp-yen { font-size: 24px; font-weight: 800; color: #333; }
.pp-price-input {
  width: 110px;
  border: none;
  border-bottom: 3px solid var(--g);
  background: transparent;
  outline: none;
  text-align: center;
  font-size: 44px;
  font-weight: 800;
  color: var(--g);
}
.pp-unit { border: none; background: transparent; font-size: 16px; font-weight: 800; color: #333; outline: none; }

.pp-action {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 12px 20px calc(20px + env(safe-area-inset-bottom));
  background: #fff;
  border-top: 1px solid #eef0f3;
  z-index: 30;
}
.pp-tip { text-align: center; font-size: 13px; font-weight: 700; color: var(--g-text); margin-bottom: 10px; }
.pp-next {
  width: 100%;
  height: 54px;
  border-radius: 14px;
  border: none;
  background: var(--g);
  color: #fff;
  font-size: 19px;
  font-weight: 800;
  box-shadow: 0 6px 18px rgba(0, 200, 83, 0.25);
}
.pp-next:disabled { opacity: 0.65; }
</style>
