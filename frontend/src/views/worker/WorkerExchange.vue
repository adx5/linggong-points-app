<!-- (积分商城：扣除积分兑换实物) -->
<template>
  <div class="exchange-page">
    <div class="header">
      <h2>积分商城</h2>
    </div>

    <div class="list">
      <div class="item">
        <div class="info">
          <h3>生活抽纸一提</h3>
          <p>生活必需品</p>
        </div>
        <div class="action">
          <span class="price">50 积分</span>
          <button @click="exchange" class="btn-ex">兑换</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import api from '../../api'

const exchange = async () => {
  try {
    const res = await api.post('/user/exchange')
    window.$toast(res.message)
  } catch (err) {
    window.$toast('积分不足或兑换失败')
  }
}
</script>

<style scoped>
.exchange-page { min-height: 100vh; background: #f5f6f8; }
.header { background: #fff; padding: 16px; border-bottom: 1px solid #eee; }
.header h2 { font-size: 18px; }
.list { padding: 12px; }
.item { background: #fff; border-radius: 8px; padding: 16px; display: flex; justify-content: space-between; align-items: center; }
.info h3 { font-size: 16px; margin-bottom: 4px; }
.info p { font-size: 12px; color: #999; }
.action { display: flex; align-items: center; gap: 12px; }
.price { color: #ef4444; font-weight: bold; }
.btn-ex { background: #2563eb; color: #fff; border: none; padding: 6px 16px; border-radius: 6px; }
</style>