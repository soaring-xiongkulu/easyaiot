import type { AppRouteModule } from '@/router/types';
import { LAYOUT } from '@/router/constant';

const edgeSelfMonitor: AppRouteModule = {
  path: '/edge-self-monitor',
  name: 'EdgeSelfMonitor',
  component: LAYOUT,
  redirect: '/edge-self-monitor/index',
  meta: {
    orderNo: 24,
    icon: 'ant-design:dashboard-outlined',
    title: '本机监测',
    hideChildrenInMenu: true,
  },
  children: [
    {
      path: 'index',
      name: 'EdgeSelfMonitorIndex',
      component: () => import('@/views/edge-self-monitor/index.vue'),
      meta: {
        title: '本机监测',
        icon: 'ant-design:dashboard-outlined',
        hideMenu: true,
      },
    },
  ],
};

export default edgeSelfMonitor;
