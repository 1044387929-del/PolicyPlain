import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { useUserStore } from '@/stores/user'

class HttpRequest {
  private instance: AxiosInstance
  public baseURL: string

  constructor() {
    const baseURL = import.meta.env.VITE_API_BASE_URL
    this.baseURL = baseURL
    this.instance = axios.create({
      baseURL,
      timeout: 180000,
    })
    this.initializeInterceptors()
  }

  private initializeInterceptors() {
    this.instance.interceptors.request.use(
      (config) => {
        const userStore = useUserStore()
        const token = userStore.accessToken
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error),
    )
    this.instance.interceptors.response.use(
      (response) => response.data,
      (error) => Promise.reject(error),
    )
  }

  public request<T = unknown>(config: AxiosRequestConfig): Promise<T> {
    return this.instance.request<any, T>(config)
  }

  public get<T = unknown>(url: string, params?: object, config?: AxiosRequestConfig): Promise<T> {
    return this.request({ ...config, url, method: 'GET', params })
  }

  public post<T = unknown>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> {
    return this.request({ ...config, url, method: 'POST', data })
  }
}

export default new HttpRequest()
