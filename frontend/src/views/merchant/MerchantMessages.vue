<!-- (B端消息通知：真实数据) -->
<template>
  <div class="msg-page">
    <div class="sticky-header">
      <h2>消息通知</h2>
      <button class="btn-read-all" @click="readAll">全部已读</button>
    </div>

    <div class="list">
      <div class="msg-card" v-for="msg in messages" :key="msg.id" :class="{ unread: !msg.is_read }" @click="readMsg(msg)">
        <div class="msg-icon">
          <span v-if="msg.title.includes('驳回')">❌</span>
          <span v-else-if="msg.title.includes('通过')">✅</span>
          <span v-else>💬</span>
        </div>
        <div class="msg-content">
          <div class="msg-title">
            <h3>{{ msg.title }}</h3>
            <span class="time">{{ formatTime(msg.created_at) }}</span>
          </div>
          <p class="msg-desc">{{ msg.content }}</p>
        </div>
      </div>
      <div v-if="messages.length === 0" class="empty">暂无消息通知</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const messages = ref([])

const loadMessages = async () => {
  try {
    const res = await api.get('/notifications/list')
    messages.value = res.data
  } catch (err) { window.$toast('获取消息失败') }
}

const readMsg = async (msg) => {
  if (msg.is_read) return
  try {
    await api.put(`/notifications/read/${msg.id}`)
    msg.is_read = true
  } catch (err) {}
}

const readAll = async () => {
  try {
    await api.put('/notifications/read-all')
    messages.value.forEach(m => m.is_read = true)
    window.$toast('已全部标记为已读')
  } catch (err) {}
}

const formatTime = (isoStr) => {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleDateString()
}

onMounted(() => { loadMessages() })
</script>

<style scoped>
.msg-page { min-height: 100vh; background: #f0f2f5; }
.sticky-header { position: sticky; top: 0; z-index: 99; background: #fff; padding: 16px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
.sticky-header h2 { font-size: 18px; color: #1f2937; }
.btn-read-all { background: transparent; border: 1px solid #2563eb; color: #2563eb; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; cursor: pointer; }
.list { padding: 16px; }
.msg-card { display: flex; gap: 12px; background: #fff; padding: 16px; border-radius: 12px; margin-bottom: 12px; position: relative; cursor: pointer; }
.msg-card.unread::after { content: ''; position: absolute; top: 16px; right: 16px; width: 8px; height: 8px; background: #ef4444; border-radius: 50%; }
.msg-icon { width: 40px; height: 40px; background: #f3f4f6; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 20px; flex-shrink: 0; }
.msg-content { flex: 1; }
.msg-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.msg-title h3 { font-size: 15px; color: #1f2937; font-weight: bold; }
.msg-title .time { font-size: 12px; color: #9ca3af; margin-right: 12px; }
.msg-desc { font-size: 13px; color: #666; line-height: 1.5; }
.empty { text-align: center; color: #999; padding: 40px; font-size: 14px; }
</style>