// frontend/src/utils/favorites.js
// 岗位收藏：本地存储（无需登录、无后端依赖），后续可迁移到账号维度
const KEY = 'job_favorites'

export function getFavoriteIds() {
  try {
    const raw = localStorage.getItem(KEY)
    const arr = raw ? JSON.parse(raw) : []
    return Array.isArray(arr) ? arr.map(String) : []
  } catch (e) {
    return []
  }
}

export function isFavorite(id) {
  return getFavoriteIds().includes(String(id))
}

/** 切换收藏，返回切换后是否已收藏 */
export function toggleFavorite(id) {
  const key = String(id)
  const list = getFavoriteIds()
  const idx = list.indexOf(key)
  if (idx >= 0) list.splice(idx, 1)
  else list.unshift(key)
  localStorage.setItem(KEY, JSON.stringify(list))
  return idx < 0
}

export function favoriteCount() {
  return getFavoriteIds().length
}
