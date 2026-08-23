import type { AppRouteRecordRaw } from '@/router/types'
import { EXCEPTION_COMPONENT, LAYOUT, PAGE_NOT_FOUND_NAME, REDIRECT_NAME } from '@/router/constant'

// 404 on a page
export const PAGE_NOT_FOUND_ROUTE: AppRouteRecordRaw = {
  path: '/:path(.*)*',
  name: PAGE_NOT_FOUND_NAME,
  component: LAYOUT,
  meta: {
    title: 'ErrorPage',
    hideBreadcrumb: true,
    hideMenu: true,
  },
  children: [
    {
      path: '/:path(.*)*',
      name: PAGE_NOT_FOUND_NAME,
      component: EXCEPTION_COMPONENT,
      meta: {
        title: 'ErrorPage',
        hideBreadcrumb: true,
        hideMenu: true,
      },
    },
  ],
}

/** GB28181：按名称跳转（不依赖后台菜单是否配置了同名路由） */
export const GB28181_ROUTE_MODULE: AppRouteRecordRaw = {
  path: '/gb28181-view',
  component: LAYOUT,
  name: 'Gb28181ViewLayout',
  meta: {
    title: 'GB28181',
    hideMenu: true,
    hideBreadcrumb: true,
  },
  children: [
    {
      path: 'channel/:deviceIdentification',
      name: 'Gb28181Channel',
      component: () => import('@/views/gb28181/components/Channel/index.vue'),
      meta: {
        title: '通道管理',
        hideMenu: true,
        canTo: true,
      },
    },
    {
      path: 'cloud-record/:deviceId/:channelId',
      name: 'Gb28181CloudRecord',
      component: () => import('@/views/gb28181/components/CloudRecord/index.vue'),
      meta: {
        title: '云端录像',
        hideMenu: true,
        canTo: true,
      },
    },
    {
      path: 'device-record/:deviceId/:channelId',
      name: 'Gb28181DeviceRecord',
      component: () => import('@/views/gb28181/components/DeviceRecord/index.vue'),
      meta: {
        title: '设备录像',
        hideMenu: true,
        canTo: true,
      },
    },
  ],
}

/** 人脸管理独立页（从人脸库列表跳转） */
export const FACE_MANAGE_ROUTE: AppRouteRecordRaw = {
  path: '/face-manage',
  component: LAYOUT,
  name: 'FaceManageLayout',
  meta: {
    title: '人脸管理',
    hideMenu: true,
    hideBreadcrumb: true,
  },
  children: [
    {
      path: ':libraryId',
      name: 'FaceManage',
      component: () => import('@/views/face-manage/index.vue'),
      meta: {
        title: '人脸管理',
        hideMenu: true,
        canTo: true,
        activeMenu: 'camera/index',
      },
    },
  ],
}

/** 车牌管理独立页（从车牌库列表跳转） */
export const PLATE_MANAGE_ROUTE: AppRouteRecordRaw = {
  path: '/plate-manage',
  component: LAYOUT,
  name: 'PlateManageLayout',
  meta: {
    title: '车牌管理',
    hideMenu: true,
    hideBreadcrumb: true,
  },
  children: [
    {
      path: ':libraryId',
      name: 'PlateManage',
      component: () => import('@/views/plate-manage/index.vue'),
      meta: {
        title: '车牌管理',
        hideMenu: true,
        canTo: true,
        activeMenu: 'camera/index',
      },
    },
  ],
}

/** 场景姿态管理独立页 */
export const SCENARIO_POSE_MANAGE_ROUTE: AppRouteRecordRaw = {
  path: '/scenario-pose-manage',
  component: LAYOUT,
  name: 'ScenarioPoseManageLayout',
  meta: {
    title: '场景姿态管理',
    hideMenu: true,
    hideBreadcrumb: true,
  },
  children: [
    {
      path: ':libraryId',
      name: 'ScenarioPoseManage',
      component: () => import('@/views/scenario-pose-manage/index.vue'),
      meta: {
        title: '场景姿态管理',
        hideMenu: true,
        canTo: true,
        activeMenu: 'camera/index',
      },
    },
  ],
}

/** 录像空间回放独立页（从录像空间列表跳转） */
export const RECORD_SPACE_MANAGE_ROUTE: AppRouteRecordRaw = {
  path: '/record-space-manage',
  component: LAYOUT,
  name: 'RecordSpaceManageLayout',
  meta: {
    title: '录像回放',
    hideMenu: true,
    hideBreadcrumb: true,
  },
  children: [
    {
      path: ':spaceId',
      name: 'RecordSpaceManage',
      component: () => import('@/views/record-space-manage/index.vue'),
      meta: {
        title: '录像回放',
        hideMenu: true,
        canTo: true,
        ignoreKeepAlive: true,
        activeMenu: 'camera/index',
      },
    },
  ],
}

/** SAM 模型安装独立页（从数据集智能标注跳转） */
export const SAM_MODEL_SETUP_ROUTE: AppRouteRecordRaw = {
  path: '/dataset/sam-model-setup',
  component: LAYOUT,
  name: 'SamModelSetupLayout',
  meta: {
    title: 'SAM 模型安装',
    hideMenu: true,
    hideBreadcrumb: true,
  },
  children: [
    {
      path: '',
      name: 'SamModelSetup',
      component: () => import('@/views/dataset/components/AutoLabel/SamModelSetup/index.vue'),
      meta: {
        title: 'SAM 模型安装',
        hideMenu: true,
        canTo: true,
        activeMenu: 'dataset/index',
      },
    },
  ],
}

/** 算法任务业务脚本 IDE（内嵌 OpenVSCode） */
export const ALGORITHM_POST_PROCESS_IDE_ROUTE: AppRouteRecordRaw = {
  path: '/algorithm-post-process',
  component: LAYOUT,
  name: 'AlgorithmPostProcessLayout',
  meta: {
    title: '业务脚本',
    hideMenu: true,
    hideBreadcrumb: true,
  },
  children: [
    {
      path: ':taskId',
      name: 'AlgorithmPostProcessIde',
      component: () => import('@/views/system/iframe/FrameDynamic.vue'),
      meta: {
        title: '业务脚本',
        hideMenu: true,
        canTo: true,
        activeMenu: 'camera/index',
      },
    },
  ],
}

/**
 * 规则引擎 Node-RED 编辑器（iframe）
 * 与 nginx 同源代理一致：iframe 打开 /dev-api/nodeRed/#flow/:id
 * 使用独立路径，避开菜单 /rulechains/index/:id + FrameBlank 撞名导致的 404。
 */
export const RULE_CHAINS_NODERED_ROUTE: AppRouteRecordRaw = {
  path: '/rulechain-editor',
  component: LAYOUT,
  name: 'RuleChainsNodeRedLayout',
  meta: {
    title: '规则引擎',
    hideMenu: true,
    hideBreadcrumb: true,
  },
  children: [
    {
      path: ':id',
      name: 'RuleChainsNodeRed',
      component: () => import('@/views/system/iframe/FrameDynamic.vue'),
      meta: {
        title: 'EasyAIoT',
        hideMenu: true,
        hideBreadcrumb: true,
        canTo: true,
        activeMenu: '/rulechains/index',
      },
    },
  ],
}

/** 抓拍空间告警独立页（从抓拍空间列表跳转） */
export const SNAP_SPACE_MANAGE_ROUTE: AppRouteRecordRaw = {
  path: '/snap-space-manage',
  component: LAYOUT,
  name: 'SnapSpaceManageLayout',
  meta: {
    title: '抓拍空间',
    hideMenu: true,
    hideBreadcrumb: true,
  },
  children: [
    {
      path: ':spaceId',
      name: 'SnapSpaceManage',
      component: () => import('@/views/snap-space-manage/index.vue'),
      meta: {
        title: '抓拍空间',
        hideMenu: true,
        canTo: true,
        ignoreKeepAlive: true,
        activeMenu: 'camera/index',
      },
    },
  ],
}

export const REDIRECT_ROUTE: AppRouteRecordRaw = {
  path: '/redirect',
  component: LAYOUT,
  name: 'RedirectTo',
  meta: {
    title: REDIRECT_NAME,
    hideBreadcrumb: true,
    hideMenu: true,
  },
  children: [
    {
      path: '/redirect/:path(.*)/:_redirect_type(.*)/:_origin_params(.*)?',
      name: REDIRECT_NAME,
      component: () => import('@/views/base/redirect/index.vue'),
      meta: {
        title: REDIRECT_NAME,
        hideBreadcrumb: true,
      },
    },
  ],
}
