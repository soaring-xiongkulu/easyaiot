import type { AppRouteModule } from '@/router/types'

import { LAYOUT } from '@/router/constant'
import { t } from '@/hooks/web/useI18n'

const dashboard: AppRouteModule = {
  path: '/dashboard',
  name: 'Dashboard',
  component: LAYOUT,
  redirect: '/dashboard/index',
  meta: {
    orderNo: 10,
    icon: 'clarity:dashboard-line',
    title: t('routes.dashboard.dashboard'),
    hideMenu: false,
    hideChildrenInMenu: true, // 隐藏子菜单，点击直接跳转
  },
  children: [
    {
      path: 'index',
      name: 'DashboardPage',
      component: () => import('@/views/dashboard/monitor/index.vue'),
      meta: {
        title: t('routes.dashboard.dashboard'),
        icon: 'clarity:dashboard-line',
        hideMenu: true, // 子路由不在菜单中显示
        hideBreadcrumb: true,
        hideTab: true,
      },
    },
  ],
}

export default dashboard
