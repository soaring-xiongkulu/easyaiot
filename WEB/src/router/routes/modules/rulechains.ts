import type { AppRouteModule } from '@/router/types'

import { LAYOUT } from '@/router/constant'

const rulechains: AppRouteModule = {
  path: '/rulechains',
  name: 'RuleChains',
  component: LAYOUT,
  redirect: '/rulechains/index',
  meta: {
    orderNo: 20,
    hideMenu: false,
    hideChildrenInMenu: true,
  },
  children: [
    {
      path: 'index/:id(.*)',
      name: 'RuleChainsNodeRed',
      component: () => import('@/views/system/iframe/FrameDynamic.vue'),
      meta: {
        title: 'NodeRed',
        hideMenu: true,
        hideBreadcrumb: true,
      },
    },
    {
      path: 'index',
      name: 'RuleChainsIndex',
      component: () => import('@/views/rulechains/index.vue'),
      meta: {
        title: '规则链',
        hideMenu: true,
      },
    },
  ],
}

export default rulechains

