<script lang="ts" setup>
import {computed, unref} from 'vue'
import {useGlobSetting} from '@/hooks/setting'
import {useGo} from '@/hooks/web/usePage'
import {useMenuSetting} from '@/hooks/setting/useMenuSetting'
import {useDesign} from '@/hooks/web/useDesign'
import {PageEnum} from '@/enums/pageEnum'

const props = defineProps({
  // 当前父组件的主题
  theme: {type: String, validator: (v: string) => ['light', 'dark'].includes(v)},
  // 是否显示标题
  showTitle: {type: Boolean, default: true},
  // 折叠菜单时也会显示标题
  alwaysShowTitle: {type: Boolean},
})

const {prefixCls} = useDesign('app-logo')
const {getCollapsedShowTitle} = useMenuSetting()
const {title} = useGlobSetting()
const go = useGo()

const getAppLogoClass = computed(() => [prefixCls, props.theme, {'collapsed-show-title': unref(getCollapsedShowTitle)}])

const getTitleClass = computed(() => [
  `${prefixCls}__title`,
  {
    'xs:opacity-0': !props.alwaysShowTitle,
  },
])

function goHome() {
  go(PageEnum.BASE_HOME)
}
</script>

<template>
  <div class="ant-icon" :class="getAppLogoClass" @click="goHome">
    <div class="logo-icon">
      <img class="uc-logo" src="@/assets/images/logo.png"/>
    </div>
    <div v-show="showTitle" class="truncate md:opacity-100 logo-title" :class="getTitleClass">
      {{ title }}
    </div>
  </div>
</template>

<style lang="less" scoped>
.ant-icon{
  margin-top: -1.28rem;
  display: flex;
  align-items: center;
  gap:0.58rem;
  .logo-icon{
    width: 32px;height: 32px;
    .uc-logo {
      width: 100% !important;
      height: 100%;
    }
  }
  .logo-title{
    font-family: moon,sans-serif;font-size: 2rem !important;margin-top: -5px;
  }
}

@prefix-cls: ~'@{namespace}-app-logo';

.@{prefix-cls} {
  display: flex;
  align-items: center;
  padding-left: 7px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 0;

  &.light {
    border-bottom: 1px solid var(--border-color);
  }

  &.collapsed-show-title {
    padding-left: 20px;
  }

  &.dark &__title {
    color: @white;
  }

  &__title {
    font-size: 16px;
    font-weight: 700;
    line-height: normal;
    transition: all 0.5s;
  }
}
</style>
