<template>
  <!-- Echarts 全局设置 -->
  <global-setting :optionData="optionData"></global-setting>
  <CollapseItem v-for="(item, index) in seriesList" :key="index" :name="`柱状图-${index + 1}`" :expanded="true">
    <SettingItemBox name="图形">
      <SettingItem name="宽度">
        <a-input-number
          v-model:value="item.barWidth"
          :min="1"
          :max="100"
          size="small"
          placeholder="自动计算"
        ></a-input-number>
      </SettingItem>
      <SettingItem name="圆角">
        <a-input-number v-model:value="item.itemStyle.borderRadius" :min="0" size="small"></a-input-number>
      </SettingItem>
    </SettingItemBox>
    <setting-item-box name="标签">
      <setting-item>
        <a-space>
          <a-switch v-model:value="item.label.show" size="small" />
          <span>展示标签</span>
        </a-space>
      </setting-item>
      <setting-item name="大小">
        <a-input-number v-model:value="item.label.fontSize" size="small" :min="1"></a-input-number>
      </setting-item>
      <setting-item name="颜色">
        <color-picker size="small" :modes="['hex']" v-model:value="item.label.color"></color-picker>
      </setting-item>
      <setting-item name="位置">
        <a-select
          v-model:value="item.label.position"
          :options="[
            { label: 'top', value: 'top' },
            { label: 'left', value: 'left' },
            { label: 'right', value: 'right' },
            { label: 'bottom', value: 'bottom' }
          ]"
        />
      </setting-item>
    </setting-item-box>
  </CollapseItem>
</template>

<script setup lang="ts">
import { PropType, computed } from 'vue'
import { GlobalSetting, CollapseItem, SettingItemBox, SettingItem } from '@/components/Design/index'
import { GlobalThemeJsonType } from '@/settings/chartThemes/index'
import ColorPicker from '@/components/ColorPicker/ColorPicker.vue'

const props = defineProps({
  optionData: {
    type: Object as PropType<GlobalThemeJsonType>,
    required: true
  }
})

const seriesList = computed(() => {
  return props.optionData.series
})
</script>
