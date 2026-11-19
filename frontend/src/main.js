// frontend/src/main.js (前端入口)
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/base.css' // 🚨 引入全局变量
import './assets/theme.css' // 🚨 主题层：未登录蓝色 / 登录后橙色

/**
 * 同步主题：未登录 → 蓝色门面；已登录 → 橙色大字版
 * 在启动、路由切换、登录/登出后都会调用。
 */
function syncTheme() {
  const authed = !!localStorage.getItem('token')
  document.body.classList.toggle('is-authed', authed)
}

syncTheme()
router.afterEach(() => {
  syncTheme()
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
