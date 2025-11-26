<template>
  <collapse-item name="渲染器">
    <setting-item-box :alone="true">
      <template #name>
        <span>全局</span>
        <a-tooltip trigger="hover">
          <template #trigger>
            <a-icon size="21" :depth="3">
              <help-outline-icon></help-outline-icon>
            </a-icon>
          </template>
          <span>所有echarts图表组件默认都将采用所选的渲染器进行渲染</span>
        </a-tooltip>
      </template>
      <EchartsRendererSetting v-model="themeSetting.renderer" />
    </setting-item-box>
    <setting-item-box :alone="true">
      <template #name>
        <span>当前</span>
        <a-tooltip trigger="hover">
          <template #trigger>
            <a-icon size="21" :depth="3">
              <help-outline-icon></help-outline-icon>
            </a-icon>
          </template>
          <span>仅当前组件采用指定渲染器渲染</span>
        </a-tooltip>
      </template>
      <EchartsRendererSetting v-model="optionData.renderer" includeInherit />
    </setting-item-box>
  </collapse-item>
  <collapse-item v-if="title" name="标题">
    <template #header>
      <a-switch v-model:value="title.show" size="small"></a-switch>
    </template>
    <setting-item-box name="标题">
      <setting-item name="颜色">
        <color-picker v-model:value="title.textStyle.color" size="small"></color-picker>
      </setting-item>
      <setting-item name="大小">
        <a-input-number v-model:value="title.textStyle.fontSize" :min="1" size="small"></a-input-number>
      </setting-item>
    </setting-item-box>
    <setting-item-box name="副标题">
      <setting-item name="颜色">
        <color-picker size="small" v-model:value="title.subtextStyle.color"></color-picker>
      </setting-item>
      <setting-item name="大小">
        <a-input-number v-model:value="title.subtextStyle.fontSize" :min="1" size="small"></a-input-number>
      </setting-item>
    </setting-item-box>
  </collapse-item>

  <collapse-item v-if="grid" name="容器">
    <setting-item-box name="距离">
      <setting-item name="左侧距离">
        <a-input v-model:value="grid.left" size="small"></a-input>
      </setting-item>
      <setting-item name="右侧距离">
        <a-input v-model:value="grid.right" size="small"></a-input>
      </setting-item>
      <setting-item name="上侧距离">
        <a-input v-model:value="grid.top" size="small"></a-input>
      </setting-item>
      <setting-item name="下侧距离">
        <a-input v-model:value="grid.bottom" size="small"></a-input>
      </setting-item>
    </setting-item-box>
  </collapse-item>

  <collapse-item v-if="xAxis" name="X轴">
    <template #header>
      <a-switch v-model:value="xAxis.show" size="small"></a-switch>
    </template>
    <setting-item-box name="单位">
      <setting-item name="名称">
        <a-input v-model:value="xAxis.name" size="small"></a-input>
      </setting-item>
      <setting-item name="颜色">
        <color-picker size="small" v-model:value="xAxis.nameTextStyle.color"></color-picker>
      </setting-item>
      <setting-item name="大小">
        <a-input-number v-model:value="xAxis.nameTextStyle.fontSize" :min="12" size="small"></a-input-number>
      </setting-item>
      <setting-item name="偏移量">
        <a-input-number v-model:value="xAxis.nameGap" :min="5" size="small"></a-input-number>
      </setting-item>
    </setting-item-box>
    <setting-item-box name="标签">
      <setting-item name="展示">
        <a-space>
          <a-switch v-model:value="xAxis.axisLabel.show" size="small"></a-switch>
        </a-space>
      </setting-item>
      <setting-item name="颜色">
        <color-picker size="small" v-model:value="xAxis.axisLabel.color"></color-picker>
      </setting-item>
      <setting-item name="大小">
        <a-input-number v-model:value="xAxis.axisLabel.fontSize" :min="8" size="small"></a-input-number>
      </setting-item>
      <setting-item name="偏移量">
        <a-input-number v-model:value="xAxis.axisLabel.rotate" :min="-90" :max="90" size="small"></a-input-number>
      </setting-item>
    </setting-item-box>
    <setting-item-box name="轴线">
      <setting-item name="展示">
        <a-space>
          <a-switch v-model:value="xAxis.axisLine.show" size="small"></a-switch>
        </a-space>
      </setting-item>
      <setting-item name="颜色">
        <color-picker v-model:value="xAxis.axisLine.lineStyle.color" size="small"></color-picker>
      </setting-item>
      <setting-item name="粗细">
        <a-input-number v-model:value="xAxis.axisLine.lineStyle.width" :min="1" size="small"></a-input-number>
      </setting-item>
      <setting-item name="位置">
        <a-select v-model:value="xAxis.position" size="small" :options="axisConfig.xposition"></a-select>
      </setting-item>
      <setting-item name="对齐零">
        <a-space>
          <a-switch v-model:value="xAxis.axisLine.onZero" size="small"></a-switch>
        </a-space>
      </setting-item>
      <setting-item name="反向">
        <a-space>
          <a-switch v-model:value="xAxis.inverse" size="small"></a-switch>
        </a-space>
      </setting-item>
    </setting-item-box>
    <setting-item-box name="刻度">
      <setting-item name="展示">
        <a-space>
          <a-switch v-model:value="xAxis.axisTick.show" size="small"></a-switch>
        </a-space>
      </setting-item>
      <setting-item name="长度">
        <a-input-number v-model:value="xAxis.axisTick.length" :min="1" size="small"></a-input-number>
      </setting-item>
    </setting-item-box>
    <setting-item-box name="分割线">
      <setting-item name="展示">
        <a-space>
          <a-switch v-model:value="xAxis.splitLine.show" size="small"></a-switch>
        </a-space>
      </setting-item>
      <setting-item name="颜色">
        <color-picker v-model:value="xAxis.splitLine.lineStyle.color" size="small"></color-picker>
      </setting-item>
      <setting-item name="粗细">
        <a-input-number v-model:value="xAxis.splitLine.lineStyle.width" :min="1" size="small"></a-input-number>
      </setting-item>
      <setting-item name="类型">
        <a-select
          v-model:value="xAxis.splitLine.lineStyle.type"
          size="small"
          :options="axisConfig.splitLint.lineStyle.type"
        ></a-select>
      </setting-item>
    </setting-item-box>
  </collapse-item>

  <collapse-item v-if="yAxis" name="Y轴">
    <template #header>
      <a-switch v-model:value="yAxis.show" size="small"></a-switch>
    </template>
    <setting-item-box name="单位">
      <setting-item name="名称">
        <a-input v-model:value="yAxis.name" size="small"></a-input>
      </setting-item>
      <setting-item name="颜色">
        <color-picker size="small" v-model:value="yAxis.nameTextStyle.color"></color-picker>
      </setting-item>
      <setting-item name="大小">
        <a-input-number v-model:value="yAxis.nameTextStyle.fontSize" :min="8" size="small"></a-input-number>
      </setting-item>
      <setting-item name="偏移量">
        <a-input-number v-model:value="yAxis.nameGap" :min="5" size="small"></a-input-number>
      </setting-item>
    </setting-item-box>
    <setting-item-box name="标签">
      <setting-item name="展示">
        <a-space>
          <a-switch v-model:value="yAxis.axisLabel.show" size="small"></a-switch>
        </a-space>
      </setting-item>
      <setting-item name="颜色">
        <color-picker size="small" v-model:value="yAxis.axisLabel.color"></color-picker>
      </setting-item>
      <setting-item name="大小">
        <a-input-number v-model:value="yAxis.axisLabel.fontSize" :min="8" size="small"></a-input-number>
      </setting-item>
      <setting-item name="偏移量">
        <a-input-number v-model:value="yAxis.axisLabel.rotate" :min="-90" :max="90" size="small"></a-input-number>
      </setting-item>
    </setting-item-box>
    <setting-item-box name="轴线">
      <setting-item name="展示">
        <a-space>
          <a-switch v-model:value="yAxis.axisLine.show" size="small"></a-switch>
        </a-space>
      </setting-item>
      <setting-item name="颜色">
        <color-picker v-model:value="yAxis.axisLine.lineStyle.color" size="small"></color-picker>
      </setting-item>
      <setting-item name="粗细">
        <a-input-number v-model:value="yAxis.axisLine.lineStyle.width" :min="1" size="small"></a-input-number>
      </setting-item>
      <setting-item name="位置">
        <a-select v-model:value="yAxis.position" size="small" :options="axisConfig.yposition"></a-select>
      </setting-item>
      <setting-item name="对齐零">
        <a-space>
          <a-switch v-model:value="yAxis.axisLine.onZero" size="small"></a-switch>
        </a-space>
      </setting-item>
      <setting-item name="反向">
        <a-space>
          <a-switch v-model:value="yAxis.inverse" size="small"></a-switch>
        </a-space>
      </setting-item>
    </setting-item-box>
    <setting-item-box name="刻度">
      <setting-item name="展示">
        <a-space>
          <a-switch v-model:value="yAxis.axisTick.show" size="small"></a-switch>
        </a-space>
      </setting-item>
      <setting-item name="长度">
        <a-input-number v-model:value="yAxis.axisTick.length" :min="1" size="small"></a-input-number>
      </setting-item>
    </setting-item-box>
    <setting-item-box name="分割线">
      <setting-item name="展示">
        <a-space>
          <a-switch v-model:value="yAxis.splitLine.show" size="small"></a-switch>
        </a-space>
      </setting-item>
      <setting-item name="颜色">
        <color-picker v-model:value="yAxis.splitLine.lineStyle.color" size="small"></color-picker>
      </setting-item>
      <setting-item name="粗细">
        <a-input-number v-model:value="yAxis.splitLine.lineStyle.width" :min="1" size="small"></a-input-number>
      </setting-item>
      <setting-item name="类型">
        <a-select
          v-model:value="yAxis.splitLine.lineStyle.type"
          size="small"
          :options="axisConfig.splitLint.lineStyle.type"
        ></a-select>
      </setting-item>
    </setting-item-box>
  </collapse-item>

  <collapse-item v-if="legend" name="图例">
    <template #header>
      <a-switch v-model:value="legend.show" size="small"></a-switch>
    </template>
    <setting-item-box name="图例文字">
      <setting-item name="颜色">
        <color-picker size="small" v-model:value="legend.textStyle.color"></color-picker>
      </setting-item>
      <setting-item name="大小">
        <a-input-number v-model:value="legend.textStyle.fontSize" :min="1" size="small"></a-input-number>
      </setting-item>
    </setting-item-box>
    <setting-item-box name="图例位置">
      <setting-item name="x轴">
        <a-select v-model:value="legend.x" size="small" :options="legendConfig.lengendX" />
      </setting-item>
      <setting-item name="y轴">
        <a-select v-model:value="legend.y" size="small" :options="legendConfig.lengendY" />
      </setting-item>
    </setting-item-box>
    <setting-item-box name="图例信息">
      <setting-item name="方向">
        <a-select v-model:value="legend.orient" size="small" :options="legendConfig.orient" />
      </setting-item>
      <setting-item name="形状">
        <a-select v-model:value="legend.icon" size="small" :options="legendConfig.shape" />
      </setting-item>
    </setting-item-box>
    <setting-item-box name="图例大小">
      <setting-item name="宽">
        <a-input-number v-model:value="legend.itemWidth" :min="1" size="small"></a-input-number>
      </setting-item>
      <setting-item name="高">
        <a-input-number v-model:value="legend.itemHeight" :min="1" size="small"></a-input-number>
      </setting-item>
    </setting-item-box>
  </collapse-item>

  <collapse-item v-if="visualMap" name="视觉映射">
    <template #header>
      <a-switch v-model:value="visualMap.show" size="small"></a-switch>
    </template>

    <setting-item-box name="范围">
      <setting-item name="最小值">
        <a-input-number v-model:value="visualMap.min" size="small"></a-input-number>
      </setting-item>
      <setting-item name="最大值">
        <a-input-number v-model:value="visualMap.max" size="small"></a-input-number>
      </setting-item>
    </setting-item-box>

    <setting-item-box name="颜色">
      <setting-item :name="`层级-${index + 1}`" v-for="(item, index) in visualMap.inRange.color" :key="index">
        <a-color-picker v-model:value="visualMap.inRange.color[index]" size="small"></a-color-picker>
      </setting-item>
    </setting-item-box>

    <setting-item-box name="控制块">
      <setting-item name="放置方向">
        <a-select v-model:value="visualMap.orient" size="small" :options="axisConfig.visualMap.orient"></a-select>
      </setting-item>
      <setting-item name="宽度">
        <a-input-number v-model:value="visualMap.itemWidth" :min="5" size="small"></a-input-number>
      </setting-item>
      <setting-item name="高度">
        <a-input-number v-model:value="visualMap.itemHeight" :min="5" size="small"></a-input-number>
      </setting-item>
      <setting-item name="反转">
        <a-space>
          <a-switch v-model:value="visualMap.inverse" size="small"></a-switch>
        </a-space>
      </setting-item>
      <setting-item name="拖拽组件实时更新">
        <a-space>
          <a-switch v-model:value="visualMap.realtime" size="small"></a-switch>
        </a-space>
      </setting-item>
    </setting-item-box>
    <global-setting-position :targetData="visualMap"></global-setting-position>
  </collapse-item>
</template>

<script setup lang="ts">
import { PropType, computed, watch } from 'vue'
import { GlobalThemeJsonType } from '@/settings/chartThemes'
import { axisConfig, legendConfig } from '@/design/packages/chartConfiguration/echarts/index'
import { CollapseItem, SettingItemBox, SettingItem, GlobalSettingPosition } from '@/components/Design/index'
import { icon } from '@/design/component'
import { useChartEditStore } from '@/store/modules/chartEditStore/chartEditStore'
import EchartsRendererSetting from './EchartsRendererSetting.vue'
import ColorPicker from '@/components/ColorPicker/ColorPicker.vue'

const { HelpOutlineIcon } = icon.ionicons5

const props = defineProps({
  optionData: {
    type: Object as PropType<GlobalThemeJsonType>,
    required: true
  },
  inChart: {
    type: Boolean,
    required: false,
    default: false
  }
})

const chartEditStore = useChartEditStore()
const themeSetting = computed(() => {
  const chartThemeSetting = chartEditStore.getEditCanvasConfig.chartThemeSetting
  return chartThemeSetting
})

const title = computed(() => {
  return props.optionData.title
})

const xAxis = computed(() => {
  return props.optionData.xAxis
})

const yAxis = computed(() => {
  return props.optionData.yAxis
})

const legend = computed(() => {
  return props.optionData.legend
})

const grid = computed(() => {
  return props.optionData.grid
})

const visualMap = computed(() => {
  return props.optionData.visualMap
})

// 监听legend color颜色改变type = scroll的颜色
watch(() => legend.value && legend.value.textStyle.color, (newVal) => {
  if (legend.value && newVal) {
     if (!legend.value.pageTextStyle) {
      legend.value.pageTextStyle = { color: newVal }
    } else {
      legend.value.pageTextStyle.color = newVal
    }
  }
}, {
  immediate: true,
  deep: true,
})
</script>
