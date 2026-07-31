import type { AppRouteModule } from '@/router/types'
import { LAYOUT } from '@/router/constant'

const transform: AppRouteModule = {
  path: '/transform',
  name: 'TransformManage',
  component: LAYOUT,
  redirect: '/transform/index',
  meta: {
    orderNo: 10,
    icon: 'ant-design:send-outlined',
    title: '数据转发',
    hideChildrenInMenu: true,
  },
  children: [
    {
      path: 'index',
      name: 'Transform',
      component: () => import('@/views/transform/index.vue'),
      meta: {
        title: '数据转发',
        icon: 'ant-design:send-outlined',
        hideMenu: true,
      },
    },
  ],
}

export default transform
