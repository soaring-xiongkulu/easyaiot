/**
 * 请求去重工具
 * 确保相同参数的请求在同一时间只发送一次，后续请求会复用第一个请求的结果
 */

// 存储正在进行的请求
const pendingRequests = new Map<string, Promise<any>>()

/**
 * 生成请求的唯一键
 * @param url 请求URL
 * @param params 请求参数
 * @returns 唯一键
 */
function generateRequestKey(url: string, params?: any): string {
  const paramsStr = params ? JSON.stringify(params) : ''
  return `${url}${paramsStr}`
}

/**
 * 带去重的请求函数
 * @param requestFn 原始请求函数
 * @param url 请求URL（用于生成唯一键）
 * @param params 请求参数（可选）
 * @param cacheTime 缓存时间（毫秒），默认1000ms，即1秒内相同请求会被去重
 * @returns Promise
 */
export function dedupeRequest<T = any>(
  requestFn: () => Promise<T>,
  url: string,
  params?: any,
  cacheTime: number = 1000
): Promise<T> {
  const key = generateRequestKey(url, params)
  
  // 如果已经有相同的请求正在进行，直接返回该Promise
  if (pendingRequests.has(key)) {
    return pendingRequests.get(key)!
  }
  
  // 创建新的请求Promise
  const requestPromise = requestFn()
    .then((response) => {
      // 请求成功后，延迟清除缓存，允许短时间内复用结果
      setTimeout(() => {
        pendingRequests.delete(key)
      }, cacheTime)
      return response
    })
    .catch((error) => {
      // 请求失败后立即清除缓存，允许重试
      pendingRequests.delete(key)
      throw error
    })
  
  // 存储请求Promise
  pendingRequests.set(key, requestPromise)
  
  return requestPromise
}

/**
 * 清除所有待处理的请求缓存
 */
export function clearPendingRequests() {
  pendingRequests.clear()
}

/**
 * 清除指定URL的请求缓存
 * @param url 请求URL
 * @param params 请求参数（可选）
 */
export function clearPendingRequest(url: string, params?: any) {
  const key = generateRequestKey(url, params)
  pendingRequests.delete(key)
}

