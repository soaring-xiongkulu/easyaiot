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
    // Node-RED 详情：basic.ts RULE_CHAINS_NODERED_ROUTE（绝对路径子路由，BACK 模式可用）
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
