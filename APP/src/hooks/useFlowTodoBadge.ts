import { getFlowTodoCount } from '@/api/flow'
import { useTokenStore } from '@/store/token'
import { tabbarStore } from '@/tabbar/store'

/**
 * 流程待办角标：轮询 GET /flow/task/todo-count，把待办数显示在「告警」tab 图标上
 * （设计文档 §8：APP 提醒依赖站内信红点 + 待办角标轮询）
 */
const POLL_INTERVAL = 30 * 1000
/** 告警 tab 在 tabbar 中的下标（见 src/tabbar/config.ts customTabbarList） */
const ALERT_TAB_INDEX = 2

let timer: ReturnType<typeof setInterval> | null = null

async function refreshBadge() {
  try {
    const tokenStore = useTokenStore().updateNowTime()
    if (!tokenStore.hasLogin) {
      tabbarStore.setTabbarItemBadge(ALERT_TAB_INDEX, 0)
      return
    }    const count = await getFlowTodoCount()
    tabbarStore.setTabbarItemBadge(ALERT_TAB_INDEX, Number(count) > 0 ? (Number(count) > 99 ? 99 : Number(count)) : 0)
  }
  catch {
    // 接口异常时保持原角标，不打断应用
  }
}

/** 启动轮询（App onShow 时调用，重复调用安全） */
export function startFlowTodoBadgePolling() {
  void refreshBadge()
  if (!timer) {
    timer = setInterval(() => void refreshBadge(), POLL_INTERVAL)
  }
}

/** 停止轮询（App onHide 时调用） */
export function stopFlowTodoBadgePolling() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}
