<script lang="ts" setup>
/**
 * 延迟器节点配置抽屉：固定时长 / 固定日期
 */
import { computed, ref } from 'vue'
import { DatePicker, Drawer, Form, FormItem, Input, InputNumber, RadioButton, RadioGroup, Select } from 'ant-design-vue'
import { Icon } from '@/components/Icon'
import type { SimpleFlowNode } from '../../consts'
import {
  DELAY_TYPE,
  NODE_VISUALS,
  NodeType,
  TIME_UNIT_TYPES,
} from '../../consts'
import { buildTimeDuration, parseTimeDuration } from '../../helpers'

defineOptions({ name: 'FlowDelayTimerNodeConfig' })

const props = defineProps<{ node: SimpleFlowNode }>()

const visible = ref(false)

function open() {
  visible.value = true
}

defineExpose({ open })

const node = computed(() => props.node)
const visual = NODE_VISUALS[NodeType.DELAY_TIMER_NODE]

const setting = computed(() => {
  if (!node.value.delaySetting) {
    node.value.delaySetting = { delayType: 1, delayTime: 'PT1H' }
  }
  return node.value.delaySetting
})

const duration = computed(() => parseTimeDuration(setting.value.delayTime))
const durationValue = ref(duration.value.value)
const durationUnit = ref(duration.value.unit)

function syncDuration() {
  setting.value.delayTime = buildTimeDuration(durationValue.value || 1, durationUnit.value)
}

function handleDelayTypeChange() {
  setting.value.delayTime = setting.value.delayType === 1 ? 'PT1H' : ''
}
</script>

<template>
  <Drawer v-model:open="visible" width="520" title="延迟器配置">
    <div class="config-head">
      <div class="config-head__icon" :style="{ backgroundColor: visual.color }">
        <Icon :icon="visual.icon" />
      </div>
      <Input v-model:value="node.name" placeholder="节点名称" />
    </div>

    <Form layout="vertical">
      <FormItem label="延迟类型">
        <RadioGroup v-model:value="setting.delayType" button-style="solid" @change="handleDelayTypeChange">
          <RadioButton v-for="item in DELAY_TYPE" :key="item.value" :value="item.value">
            {{ item.label }}
          </RadioButton>
        </RadioGroup>
      </FormItem>
      <FormItem v-if="setting.delayType === 1" label="延迟时长">
        <div style="display: flex; gap: 8px">
          <InputNumber v-model:value="durationValue" :min="1" style="flex: 1" @change="syncDuration" />
          <Select v-model:value="durationUnit" :options="TIME_UNIT_TYPES" style="width: 100px" @change="syncDuration" />
        </div>
      </FormItem>
      <FormItem v-else label="固定日期时间">
        <DatePicker
          show-time
          value-format="YYYY-MM-DD HH:mm:ss"
          :value="setting.delayTime"
          style="width: 100%"
          placeholder="选择到达该时间后继续流转"
          @change="(value: string) => (setting.delayTime = value ?? '')"
        />
      </FormItem>
    </Form>
  </Drawer>
</template>

<style scoped>
.config-head {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 16px;
}

.config-head__icon {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  color: #fff;
  flex-shrink: 0;
}
</style>
