// (跨端存储适配层：目前使用 localStorage，未来可无缝切换为 uni.setStorageSync)

const isMiniProgram = typeof window === 'undefined' || !window.localStorage

export const storage = {
  set(key, value) {
    if (isMiniProgram) {
      // uni.setStorageSync(key, value)
    } else {
      if (typeof value === 'object') {
        localStorage.setItem(key, JSON.stringify(value))
      } else {
        localStorage.setItem(key, value)
      }
    }
  },

  get(key) {
    if (isMiniProgram) {
      // return uni.getStorageSync(key)
    } else {
      const val = localStorage.getItem(key)
      try {
        return JSON.parse(val)
      } catch {
        return val
      }
    }
  },

  remove(key) {
    if (isMiniProgram) {
      // uni.removeStorageSync(key)
    } else {
      localStorage.removeItem(key)
    }
  },

  clear() {
    if (isMiniProgram) {
      // uni.clearStorageSync()
    } else {
      localStorage.clear()
    }
  }
}