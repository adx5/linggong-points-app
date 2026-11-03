// frontend/src/api/index.js (Axios封装：游客自动注入默认城市)
import axios from 'axios'
import router from '../router'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  // 🚨 核心修复：游客和 C 端请求，如果没有城市，自动注入默认城市(登封 410185)
  if (!config.headers['X-City-Id']) {
    const guestCity = localStorage.getItem('guest_city_id') || '410185'
    config.headers['X-City-Id'] = guestCity
  }

  return config
}, error => {
  return Promise.reject(error)
})

api.interceptors.response.use(
  res => {
    if (res.data && res.data.code !== 0 && res.data.code !== 200) {
      if (window.$toast) window.$toast(res.data.message || '请求失败')
      return Promise.reject(new Error(res.data.message || 'Error'))
    }
    return res.data
  },
  err => {
    if (err.response) {
      const status = err.response.status
      const msg = err.response.data?.detail || '请求失败'

      if (status === 401) {
        const requireAuthPaths = ['/api/merchant', '/api/admin', '/api/user', '/api/jobs/apply']
        const isAuthAction = requireAuthPaths.some(path => err.config.url.includes(path))

        if (isAuthAction || router.currentRoute.value.meta.requireAuth) {
          if (window.$toast) window.$toast('登录状态已失效')
          localStorage.clear()
          if (router.currentRoute.value.path !== '/login') {
            window.location.href = '/login'
          }
        } else {
          console.warn('游客浏览受限接口，已拦截重定向')
        }
      } else if (status === 400 && msg.includes('未开放')) {
        window.$toast(msg)
        localStorage.removeItem('guest_city_id')
        setTimeout(() => window.location.reload(), 1000)
      } else if (status === 403) {
        if (window.$toast) window.$toast(`权限不足：${msg}`)
      } else {
        if (window.$toast) window.$toast(msg)
      }
    } else {
      if (window.$toast) window.$toast('网络连接失败')
    }
    return Promise.reject(err)
  }
)

export default api