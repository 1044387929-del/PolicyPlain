import request from '@/apis/request'

export interface PolicyUser {
  id: string
  email: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  user: PolicyUser
  token_type?: string
}

export function sendRegisterCode(data: { email: string }) {
  return request.post<{ result: string; expires_in: number; resend_after: number }>(
    '/user/register/send-code',
    data,
  )
}

export function register(data: {
  email: string
  password: string
  password_confirm: string
  invite_code: string
}) {
  return request.post<{ result: string }>('/user/register', data)
}

export function login(data: { email: string; password: string }) {
  return request.post<LoginResponse>('/user/login', data)
}

export function fetchMe() {
  return request.get<PolicyUser>('/user/me')
}
