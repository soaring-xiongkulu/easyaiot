import type { AppRouteModule } from '@/router/types'
import { LAYOUT } from '@/router/constant'

const idea: AppRouteModule = {
  path: '/idea',
  name: 'IdeaManage',
  component: LAYOUT,
  redirect: '/idea/index',
  meta: {
    orderNo: 95,
    icon: 'ant-design:code-outlined',
    title: '在线IDEA',
    hideChildrenInMenu: true,
  },
  children: [
    {
      path: 'index',
      name: 'IdeaPortal',
      component: () => import('@/views/idea/index.vue'),
      meta: {
        title: '在线IDEA',
        icon: 'ant-design:code-outlined',
        hideMenu: true,
      },
    },
  ],
}

export default idea
