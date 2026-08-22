import type { AppRouteModule } from '@/router/types';
import { LAYOUT } from '@/router/constant';

const postPlugin: AppRouteModule = {
  path: '/post-plugin',
  name: 'PostPluginManageRoot',
  component: LAYOUT,
  redirect: '/post-plugin/index',
  meta: {
    orderNo: 26,
    icon: 'ant-design:api-outlined',
    title: '后处理插件',
    hideChildrenInMenu: true,
  },
  children: [
    {
      path: 'index',
      name: 'PostPluginManage',
      component: () => import('@/views/post/PostPluginManage.vue'),
      meta: {
        title: '后处理插件',
        icon: 'ant-design:api-outlined',
        hideMenu: true,
      },
    },
  ],
};

export default postPlugin;
