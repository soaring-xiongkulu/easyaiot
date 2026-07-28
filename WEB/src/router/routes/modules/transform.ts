import type { AppRouteModule } from '@/router/types'
import { LAYOUT } from '@/router/constant'

const transform: AppRouteModule = {
  path: '/transform',
  name: 'TransformManage',
  component: LAYOUT,
  redirect: '/transform/index',
  meta: {
    orderNo: 47,
    icon: 'ant-design:api-outlined',
    title: '系统对接',
    hideChildrenInMenu: true,
  },
  children: [
    {
      path: 'index',
      name: 'Transform',
      component: () => import('@/views/transform/index.vue'),
      meta: {
        title: '系统对接',
        icon: 'ant-design:api-outlined',
        hideMenu: true,
      },
    },
  ],
}

export default transform
