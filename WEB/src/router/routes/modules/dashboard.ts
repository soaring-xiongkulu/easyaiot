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
  },
  children: [
    {
      path: 'index',
      name: '_Dashboard',
      component: () => import('@/views/dashboard/analysis/index.vue'),
      meta: {
        title: t('routes.dashboard.analysis'),
        icon: 'clarity:dashboard-line',
        hideMenu: true,
      },
    },
  ],
}

export default dashboard
