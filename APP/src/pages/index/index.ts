import { useAccess } from '@/hooks/useAccess'

/**
 * 工作台菜单数据
 * 定义菜单分组和菜单项的数据结构
 */

/** 菜单项类型 */
export interface MenuItem {
  key: string // 菜单唯一标识
  name: string // 菜单名称
  icon: string // 菜单图标（支持 @wot-ui/ui 图标名或图片路径）
  url?: string // 跳转路径
  iconColor?: string // 图标颜色（可选）
  enabled?: boolean // 是否启用（可选，默认 true）
  permission?: string // 权限标识（可选）
}

/** 菜单分组类型 */
export interface MenuGroup {
  key: string // 分组唯一标识
  name: string // 分组名称
  menus: MenuItem[] // 分组下的菜单列表
}

/** 菜单分组原始数据（仅保留 APP 内仍存在的页面） */
const menuGroupsData: MenuGroup[] = [
  {
    key: 'easyaiot',
    name: 'EasyAIoT',
    menus: [
      {
        key: 'device',
        name: '设备管理',
        icon: 'video-camera',
        url: '/pages/device/index',
        iconColor: '#2f6bff',
      },
      {
        key: 'deviceConsole',
        name: '设备控制台',
        icon: 'apps',
        url: '/pages/device/console/index',
        iconColor: '#6fa8ff',
      },
      {
        key: 'streamForward',
        name: '推流管理',
        icon: 'share-external',
        url: '/pages/stream-forward/index',
        iconColor: '#13c2c2',
      },
      {
        key: 'algorithm',
        name: '算法管理',
        icon: 'experiment',
        url: '/pages/algorithm/index',
        iconColor: '#722ed1',
      },
      {
        key: 'alert',
        name: '告警管理',
        icon: 'exclamation-circle',
        url: '/pages/alert/index',
        iconColor: '#fa8c16',
      },
      {
        key: 'model',
        name: '模型管理',
        icon: 'module-fill',
        url: '/pages/model/index',
        iconColor: '#2f54eb',
      },
      {
        key: 'inference',
        name: '在线推理',
        icon: 'lightning-circle-fill',
        url: '/pages/inference/index',
        iconColor: '#52c41a',
      },
      {
        key: 'train',
        name: '模型训练',
        icon: 'time-line',
        url: '/pages/train/index',
        iconColor: '#eb2f96',
      },
    ],
  },
  {
    key: 'deviceAccess',
    name: '设备接入',
    menus: [
      {
        key: 'gb28181',
        name: 'GB28181',
        icon: 'camera',
        url: '/pages/device/gb28181/index',
        iconColor: '#1677ff',
      },
      {
        key: 'nvr',
        name: 'NVR 设备',
        icon: 'list',
        url: '/pages/device/nvr/index',
        iconColor: '#36cfc9',
      },
    ],
  },
  {
    key: 'user',
    name: '个人',
    menus: [
      {
        key: 'contact',
        name: '联系客服',
        icon: 'phone',
        url: '/pages/contact/index',
        iconColor: '#13c2c2',
      },
      {
        key: 'userCenter',
        name: '个人中心',
        icon: 'user',
        url: '/pages/user/index',
        iconColor: '#1890ff',
      },
    ],
  },
]

/** 全局菜单分组展示顺序 */
const GROUP_ORDER = [
  'easyaiot',
  'deviceAccess',
  'user',
]

/** 分组内菜单展示顺序（未列出的分组保持原顺序） */
const MENU_ORDER: Record<string, string[]> = {}

/** 取在顺序数组中的下标，未列出的排到最后 */
function orderIndex(order: string[], key: string) {
  const index = order.indexOf(key)
  return index === -1 ? order.length : index
}

/**
 * 获取所有菜单分组数据（带权限过滤）：过滤掉没有权限的菜单项，如果整个分组都没有权限则不展示该分组
 */
export function getMenuGroups(): MenuGroup[] {
  const { hasAccessByCodes } = useAccess()
  return menuGroupsData
    .map((group) => {
      const menus = group.menus.filter((menu) => {
        if (!menu.permission) {
          return true
        }
        return hasAccessByCodes([menu.permission])
      })
      const order = MENU_ORDER[group.key]
      if (order) {
        menus.sort((a, b) => orderIndex(order, a.key) - orderIndex(order, b.key))
      }
      return { ...group, menus }
    })
    .filter(group => group.menus.length > 0)
    .sort((a, b) => GROUP_ORDER.indexOf(a.key) - GROUP_ORDER.indexOf(b.key))
}

/** 获取所有菜单项（扁平化） */
export function getAllMenuItems(): MenuItem[] {
  const groups = getMenuGroups()
  return groups.flatMap(group => group.menus)
}

/** 根据 key 获取菜单项 */
export function getMenuItemByKey(key: string): MenuItem | undefined {
  return getAllMenuItems().find(item => item.key === key)
}
