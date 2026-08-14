import type { AppRouteModule } from '@/router/types'
import { LAYOUT } from '@/router/constant'

const harness: AppRouteModule = {
  path: '/harness',
  name: 'HarnessManage',
  component: LAYOUT,
  redirect: '/harness/index',
  meta: {
    orderNo: 96,
    icon: 'ant-design:robot-outlined',
    title: 'AI助手',
    hideChildrenInMenu: true,
  },
  children: [
    {
      path: 'index',
      name: 'HarnessPortal',
      component: () => import('@/views/harness/index.vue'),
      meta: {
        title: 'AI助手',
        icon: 'ant-design:robot-outlined',
        hideMenu: true,
      },
    },
  ],
}

export default harness
