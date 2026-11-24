import type { AppRouteModule } from '@/router/types';
import { LAYOUT } from '@/router/constant';

const edgeComputing: AppRouteModule = {
  path: '/edge-computing',
  name: 'EdgeComputing',
  component: LAYOUT,
  redirect: '/edge-computing/index',
  meta: {
    orderNo: 24,
    icon: 'ant-design:deployment-unit-outlined',
    title: '边缘计算',
    hideChildrenInMenu: true,
  },
  children: [
    {
      path: 'index',
      name: 'EdgeComputingIndex',
      component: () => import('@/views/edge-computing/index.vue'),
      meta: {
        title: '边缘计算',
        icon: 'ant-design:deployment-unit-outlined',
        hideMenu: true,
      },
    },
  ],
};

export default edgeComputing;
