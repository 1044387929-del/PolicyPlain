import request from '@/apis/request'

export interface PolicyUser {
  id: string
  username: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: PolicyUser
}

export function register(data: { username: string; password: string }) {
  return request.post<{ result: string }>('/auth/register', data)
}

export function login(data: { username: string; password: string }) {
  return request.post<LoginResponse>('/auth/login', data)
}

export function fetchMe() {
  return request.get<PolicyUser>('/users/me')
}
