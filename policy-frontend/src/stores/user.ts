import { defineStore } from 'pinia'

export interface PolicyUser {
  id: string
  email: string
}

export interface UserState {
  user: PolicyUser | null
  accessToken: string | null
}

const LS_USER = 'policy_plain_user'
const LS_TOKEN = 'policy_plain_access_token'

export const useUserStore = defineStore('user', {
  state: (): UserState => {
    const rawUser = localStorage.getItem(LS_USER)
    const accessToken = localStorage.getItem(LS_TOKEN)
    return {
      user: rawUser ? (JSON.parse(rawUser) as PolicyUser) : null,
      accessToken: accessToken || null,
    }
  },
  getters: {
    isLoggedIn(): boolean {
      return !!this.accessToken
    },
  },
  actions: {
    login(user: PolicyUser, accessToken: string) {
      this.user = user
      this.accessToken = accessToken
      localStorage.setItem(LS_USER, JSON.stringify(user))
      localStorage.setItem(LS_TOKEN, accessToken)
    },
    logout() {
      this.user = null
      this.accessToken = null
      localStorage.removeItem(LS_USER)
      localStorage.removeItem(LS_TOKEN)
    },
  },
})
