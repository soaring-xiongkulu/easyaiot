/**
 * 将 Axios / 后端错误转为面向用户的中文提示
 */
export function isNotFoundError(error: unknown): boolean {
  const err = error as { response?: { status?: number } };
  return err?.response?.status === 404;
}

export function formatApiErrorMessage(error: unknown, fallback = '操作失败，请稍后重试'): string {
  if (!error) return fallback;

  const err = error as {
    response?: { status?: number; data?: { msg?: string; message?: string } };
    data?: { msg?: string };
    msg?: string;
    code?: string;
    message?: string;
  };

  const backendMsg =
    err?.response?.data?.msg
    || err?.response?.data?.message
    || err?.data?.msg
    || err?.msg;
  if (typeof backendMsg === 'string' && backendMsg.trim()) {
    return backendMsg.trim();
  }

  const code = err?.code;
  const message = String(err?.message || '');

  if (
    code === 'ERR_NETWORK'
    || message.includes('Network Error')
    || message.includes('ERR_CONNECTION_REFUSED')
    || message.includes('Failed to fetch')
  ) {
    return '无法连接服务器，请确认 VIDEO 服务已启动且网络正常';
  }

  if (code === 'ECONNABORTED' || message.toLowerCase().includes('timeout')) {
    return '请求超时，请稍后重试';
  }

  const status = err?.response?.status;
  if (status === 404) return '请求的资源不存在，请刷新页面后重试';
  if (status === 403) return '没有操作权限';
  if (status === 401) return '登录已过期，请重新登录';
  if (status != null && status >= 500) return '服务器内部错误，请稍后重试或联系管理员';

  if (typeof error === 'string' && error.trim()) return error.trim();

  if (message && !/^Request failed with status code \d+$/.test(message)) {
    return message;
  }

  return fallback;
}
