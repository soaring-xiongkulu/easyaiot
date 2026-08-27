import type { AuthPermissionInfo, IUserInfoRes } from '@/api/types/login'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  // getUserInfo,
  getAuthPermissionInfo,
} from '@/api/login'

// 初始化状态
const userInfoState: IUserInfoRes = {
  userId: -1,
  username: '',
  nickname: '',
  avatar: '/static/images/default-avatar.png', // TODO @芋艿：CDN 化
}

export const useUserStore = defineStore(
  'user',
  () => {
    // 定义用户信息
    const userInfo = ref<IUserInfoRes>({ ...userInfoState })
    const tenantId = ref<number | null>(null) // 租户编号
    const roles = ref<string[]>([]) // 角色标识列表
    const permissions = ref<string[]>([]) // 权限标识列表
    const favoriteMenus = ref<string[]>([]) // 常用菜单 key 列表
    const favoriteMenusVersion = ref(0) // 常用菜单数据版本（0=默认策略生效前）

    /** 默认策略版本：该版本起常用菜单默认全选 */
    const FAVORITE_MENUS_DEFAULT_ALL_VERSION = 2

    /**
     * 初始化常用菜单：首次使用或旧版数据时，一次性写入全部菜单 key（即默认全选）；
     * 版本就位后以用户自选为准——包括被用户清空的场景也不会再强制回填
     */
    const initFavoriteMenus = (allKeys: string[]) => {
      if (favoriteMenusVersion.value >= FAVORITE_MENUS_DEFAULT_ALL_VERSION) {
        return
      }
      favoriteMenus.value = [...allKeys]
      favoriteMenusVersion.value = FAVORITE_MENUS_DEFAULT_ALL_VERSION
    }

    /** 设置用户信息 */
    const setUserInfo = (val: AuthPermissionInfo) => {
      // console.log('设置用户信息', val)
      // 若头像为空 则使用默认头像
      if (!val.user.avatar) {
        val.user.avatar = userInfoState.avatar
      }
      userInfo.value = val.user
      roles.value = val.roles
      permissions.value = val.permissions
    }

    const setUserAvatar = (avatar: string) => {
      userInfo.value.avatar = avatar
      // console.log('设置用户头像', avatar)
      // console.log('userInfo', userInfo.value)
    }

    /** 删除用户信息 */
    const clearUserInfo = () => {
      userInfo.value = { ...userInfoState }
      roles.value = []
      permissions.value = []
      uni.removeStorageSync('user')
    }

    /** 设置租户编号 */
    const setTenantId = (id: number) => {
      tenantId.value = id
    }

    /** 设置常用菜单 */
    const setFavoriteMenus = (keys: string[]) => {
      favoriteMenus.value = keys
    }

    /** 获取用户信息 */
    const fetchUserInfo = async () => {
      const res = await getAuthPermissionInfo()
      // 兼容：后端返回的用户 id 字段为 id
      res.user.userId = res.user.id
      setUserInfo(res)
      return res
    }

    return {
      userInfo,
      tenantId,
      roles,
      permissions,
      favoriteMenus,
      favoriteMenusVersion,
      clearUserInfo,
      fetchUserInfo,
      setUserInfo,
      setUserAvatar,
      setTenantId,
      initFavoriteMenus,
      setFavoriteMenus,
    }
  },
  {
    persist: true,
  },
)
