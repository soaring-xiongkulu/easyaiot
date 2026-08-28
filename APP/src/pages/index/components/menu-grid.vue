<template>
  <view>
    <wd-grid :column="4" clickable :border="false">
      <wd-grid-item
        v-for="menu in menus"
        :key="menu.key"
        :text="menu.name"
        @click="handleClick(menu)"
      >
        <template #icon>
          <view
            class="h-80rpx w-80rpx flex items-center justify-center rounded-20rpx"
            :style="getIconStyle(menu)"
          >
            <wd-icon :name="menu.icon" size="50rpx" :color="menu.iconColor" />
          </view>
        </template>
      </wd-grid-item>
    </wd-grid>
  </view>
</template>

<script lang="ts" setup>
import type { MenuItem } from '../index'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import { isTabBarPage } from '@/tabbar/config'
import { parseUrl, setTabParams } from '@/utils/url'

defineOptions({
  name: 'MenuGrid',
})

defineProps<{
  menus: MenuItem[] // 菜单列表
}>()

const toast = useToast()

/** 处理菜单点击 */
function handleClick(menu: MenuItem) {
  if (!menu.url) {
    toast.show('功能开发中')
    return
  }

  // 解析 URL，提取路径和参数
  const { path, query } = parseUrl(menu.url)

  // 判断是否是 tabBar 页面
  if (isTabBarPage(path)) {
    // tabBar 页面：通过 globalData 传参，使用 switchTab 跳转
    if (Object.keys(query).length > 0) {
      setTabParams(query)
    }
    uni.switchTab({
      url: path,
      fail: () => {
        toast.show('页面不存在')
      },
    })
  } else {
    // 普通页面：使用 navigateTo 跳转
    uni.navigateTo({
      url: menu.url,
      fail: () => {
        toast.show('页面不存在')
      },
    })
  }
}

/** 获取图标样式 */
function getIconStyle(menu: MenuItem) {
  return {
    backgroundColor: menu.iconColor ? `${menu.iconColor}20` : '#f5f5f5',
    color: menu.iconColor || '#666',
  }
}
</script>

<style lang="scss" scoped>
// 收窄宫格内容左右内边距：默认 padding-loose 下 4 列文字区放不下「设备控制台」这类 5 字菜单，末字会折行
:deep(.wd-grid-item__content) {
  padding: 24rpx 8rpx;
}

:deep(.wd-grid-item__text) {
  width: 100%;
  min-height: 64rpx;
  font-size: 24rpx;
  line-height: 32rpx;
  color: var(--app-text-1, #10131a);
  overflow: hidden;
  display: -webkit-box;
  white-space: normal;
  word-break: break-all;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
</style>
