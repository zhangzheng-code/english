import axios from 'axios'
import { useUserStore } from '@/stores/user' //pinia user的
import router from '@/router' //路由
import { refreshTokenApi } from './auth' //刷新token接口
import { ElMessage } from 'element-plus' //引入element-plus的提示框
export const uploadUrl = import.meta.env.VITE_MINIO_ENDPOINT

export const getFileUrl = (path: string): string => {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const base = uploadUrl.replace(/\/+$/, '')
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  return `${base}${cleanPath}`
}
export const socketUrl = import.meta.env.VITE_SOCKET_URL
export const timeout = 50000
//server服务器接口
export const serverApi = axios.create({
    baseURL: '/api/v1',
    timeout,
})
let isRefreshing = false //是否正在刷新token
let requestQueue: ((newAccessToken: string) => void)[] = [] //存储失败的请求
//请求拦截器
serverApi.interceptors.request.use(config => {
    const userStore = useUserStore()
    if (userStore.getAccessToken) {
        config.headers.Authorization = `Bearer ${userStore.getAccessToken}`
    }
    return config
})
//响应拦截器
serverApi.interceptors.response.use(res => {
    return res.data
}, async error => {
    if(error.code === "ERR_NETWORK"){
        ElMessage.error('网络连接失败,请重试')
        return Promise.reject(error)
    }
    if (error.response.status !== 401) {
        ElMessage.error('服务器异常,请稍后再试')
        //其他code码就直接抛出异常
        return Promise.reject(error)
    }
    //下面的逻辑就是处理401的情况了
    const userStore = useUserStore()
    const accessToken = userStore.getAccessToken
    const refreshToken = userStore.getRefreshToken
    const originalRequest = error.config //读取原始请求
    if (!accessToken || !refreshToken) {
        userStore.logout() //清空user
        ElMessage.error('登录已过期,请重新登录')
        router.replace('/') //跳转到首页
        return Promise.reject(error)
    }
    if (isRefreshing) {
        return new Promise((resolve) => {
            requestQueue.push((newAccessToken: string) => {
                originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
                resolve(serverApi(originalRequest))
            })
        })
    }
    //刷新token调用接口
    isRefreshing = true
    try {
        const newToken = await refreshTokenApi({ refreshToken: refreshToken })
        if (newToken.success) {
            //切换成功更新token到pinia中
            userStore.updateToken(newToken.data)
        } else {
            userStore.logout() //清空user
            ElMessage.error('登录已过期,请重新登录')
            router.replace('/') //跳转到首页
            return Promise.reject(error)
        }
        const newAccessToken = newToken.data.accessToken
        requestQueue.forEach(callback => callback(newAccessToken)) //执行存储的请求
        return serverApi(originalRequest)
    } catch (error) {
        return Promise.reject(error)
    } finally {
        requestQueue = [] //清空队列
        isRefreshing = false //重置刷新状态
    }
})
//ai服务器接口
export const aiApi = axios.create({
    baseURL: '/ai/v1',
    timeout,
})

aiApi.interceptors.request.use(config => {
    const userStore = useUserStore()
    if (userStore.getAccessToken) {
        config.headers.Authorization = `Bearer ${userStore.getAccessToken}`
    }
    // /chat 为 SSE 流式接口，严禁 Axios 超时截断——设为 0 表示永不超时
    if (config.url && config.url.includes('/chat')) {
        config.timeout = 0
    }
    return config
})

aiApi.interceptors.response.use(async response => {
    const res = response.data
    // 1. 兼容 FastAPI 的 200 OK + code=401 业务层鉴权失效响应
    if (res && res.code === 401) {
        const originalRequest = response.config
        if (originalRequest && originalRequest.url && originalRequest.url.includes('/chat')) {
            return response
        }
        const userStore = useUserStore()
        const refreshToken = userStore.getRefreshToken
        if (refreshToken) {
            try {
                if (isRefreshing) {
                    return new Promise((resolve) => {
                        requestQueue.push((newAccessToken: string) => {
                            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
                            resolve(aiApi(originalRequest))
                        })
                    })
                }
                
                isRefreshing = true
                const newToken = await refreshTokenApi({ refreshToken })
                if (newToken.success) {
                    userStore.updateToken(newToken.data)
                    isRefreshing = false
                    const newAccessToken = newToken.data.accessToken
                    requestQueue.forEach(callback => callback(newAccessToken))
                    requestQueue.length = 0
                    
                    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
                    return await aiApi(originalRequest)
                } else {
                    isRefreshing = false
                    userStore.logout()
                    router.replace('/')
                    ElMessage.error('登录已过期,请重新登录')
                    return res
                }
            } catch (e) {
                isRefreshing = false
                userStore.logout()
                router.replace('/')
                ElMessage.error('登录已过期,请重新登录')
                return Promise.reject(e)
            }
        }
    }
    return res
}, async error => {
    // 2. 兼容传统的 HTTP 401 网络层响应
    if (error.response && error.response.status === 401) {
        const originalRequest = error.config
        if (originalRequest && originalRequest.url && originalRequest.url.includes('/chat')) {
            return Promise.reject(error)
        }
        const userStore = useUserStore()
        const refreshToken = userStore.getRefreshToken
        if (refreshToken) {
            try {
                if (isRefreshing) {
                    return new Promise((resolve) => {
                        requestQueue.push((newAccessToken: string) => {
                            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
                            resolve(aiApi(originalRequest))
                        })
                    })
                }

                isRefreshing = true
                const newToken = await refreshTokenApi({ refreshToken })
                if (newToken.success) {
                    userStore.updateToken(newToken.data)
                    isRefreshing = false
                    const newAccessToken = newToken.data.accessToken
                    requestQueue.forEach(callback => callback(newAccessToken))
                    requestQueue.length = 0

                    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
                    return await aiApi(originalRequest)
                } else {
                    isRefreshing = false
                    userStore.logout()
                    router.replace('/')
                    ElMessage.error('登录已过期,请重新登录')
                    return Promise.reject(error)
                }
            } catch (e) {
                isRefreshing = false
                userStore.logout()
                router.replace('/')
                ElMessage.error('登录已过期,请重新登录')
                return Promise.reject(e)
            }
        }
    }
    return Promise.reject(error)
})


export interface Response<T = any> {
    timestamp: string,
    path: string,
    message: string,
    code: number,
    success: boolean,
    data: T
}