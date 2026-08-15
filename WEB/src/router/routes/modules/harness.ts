import type { AppRouteModule } from '@/router/types'
import { LAYOUT } from '@/router/constant'
import { getHarnessAppName } from '@/utils/harness'

const harnessTitle = getHarnessAppName()

const harness: AppRouteModule = {
  path: '/harness',
  name: 'HarnessManage',
  component: LAYOUT,
  redirect: '/harness/index',
  meta: {
    orderNo: 96,
    icon: 'ant-design:robot-outlined',
    title: harnessTitle,
    hideChildrenInMenu: true,
  },
  children: [
    {
      path: 'index',
      name: 'HarnessPortal',
      component: () => import('@/views/harness/index.vue'),
      meta: {
        title: harnessTitle,
        icon: 'ant-design:robot-outlined',
        hideMenu: true,
      },
    },
  ],
}

export default harness
