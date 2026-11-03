// (Pinia状态管理：存用户信息、所有角色、当前激活角色)
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { storage } from '../utils/storage'

export const useUserStore = defineStore('user', () => {
  const token = ref(storage.get('token') || '')
  const roles = ref(storage.get('roles') || [])
  const activeRole = ref(storage.get('activeRole') || '')

  function setLogin(data, targetRole) {
    token.value = data.token
    roles.value = data.roles
    activeRole.value = targetRole

    storage.set('token', token.value)
    storage.set('roles', roles.value)
    storage.set('activeRole', activeRole.value)
  }

  function logout() {
    storage.clear()
    window.location.href = '/login'
  }

  return { token, roles, activeRole, setLogin, logout }
})