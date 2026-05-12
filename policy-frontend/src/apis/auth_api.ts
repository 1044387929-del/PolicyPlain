import request from '@/apis/request'

export interface PolicyUser {
  id: string
  email: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: PolicyUser
}

export function sendRegisterCode(data: { email: string }) {
  return request.post<{ result: string; expires_in: number; resend_after: number }>(
    '/auth/register/send-code',
    data,
  )
}

export function register(data: {
  email: string
  password: string
  password_confirm: string
  code: string
}) {
  return request.post<{ result: string }>('/auth/register', data)
}

export function login(data: { email: string; password: string }) {
  return request.post<LoginResponse>('/auth/login', data)
}

export function fetchMe() {
  return request.get<PolicyUser>('/users/me')
}
