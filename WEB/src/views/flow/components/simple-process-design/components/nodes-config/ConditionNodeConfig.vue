<script lang="ts" setup>
/**
 * 条件（分支列头）配置抽屉：条件规则（告警变量 + 运算符 + 值）/ 条件表达式 / 默认分支
 * 数据落在 conditionSetting，规则结构与后端 ConditionGroups 契约一致。
 */
import { computed, ref } from 'vue'
import { Button, Divider, Drawer, Form, FormItem, Input, RadioButton, RadioGroup, Select, Switch } from 'ant-design-vue'
import { Icon } from '@/components/Icon'
import type { SimpleFlowNode } from '../../consts'
import { ALERT_VARIABLE_FIELDS, COMPARISON_OPERATORS, ConditionType, CONDITION_CONFIG_TYPES, NODE_VISUALS, NodeType } from '../../consts'

defineOptions({ name: 'FlowConditionNodeConfig' })

const props = defineProps<{ node: SimpleFlowNode }>()

const visible = ref(false)

function open(_target?: SimpleFlowNode) {
  visible.value = true
}

defineExpose({ open })

const node = computed(() => props.node)
const visual = NODE_VISUALS[NodeType.CONDITION_NODE]

const setting = computed(() => {
  if (!node.value.conditionSetting) {
    node.value.conditionSetting = { conditionType: ConditionType.RULE }
  }
  return node.value.conditionSetting
})

const groups = computed(() => {
  if (!setting.value.conditionGroups) {
    setting.value.conditionGroups = {
      and: true,
      conditions: [{ and: true, rules: [{ leftSide: 'alertEvent', opCode: '==', rightSide: '' }] }],
    }
  }
  return setting.value.conditionGroups
})

/** UI 只暴露第一组规则（且/或作用于组内全部规则） */
const firstCondition = computed(() => {
  if (!groups.value.conditions?.length) {
    groups.value.conditions = [{ and: true, rules: [] }]
  }
  return groups.value.conditions[0]
})

const andLabel = computed(() => (groups.value.and ? '且' : '或'))

function addRule() {
  firstCondition.value.rules.push({ leftSide: 'alertEvent', opCode: '==', rightSide: '' })
}

function removeRule(index: number) {
  firstCondition.value.rules.splice(index, 1)
}

function handleTypeChange() {
  if (setting.value.conditionType === ConditionType.EXPRESSION && !setting.value.conditionExpression) {
    setting.value.conditionExpression = "\${alertEvent == 'intrusion'}"
  }
}
</script>

<template>
  <Drawer v-model:open="visible" width="560" title="分支条件配置">
    <div class="config-head">
      <div class="config-head__icon" :style="{ backgroundColor: visual.color }">
        <Icon :icon="visual.icon" />
      </div>
      <Input v-model:value="node.name" placeholder="分支名称（如：夜间入侵）" />
    </div>

    <Form layout="vertical">
      <FormItem label="条件类型">
        <RadioGroup v-model:value="setting.conditionType" button-style="solid" @change="handleTypeChange">
          <RadioButton v-for="item in CONDITION_CONFIG_TYPES" :key="item.value" :value="item.value">
            {{ item.label }}
          </RadioButton>
        </RadioGroup>
      </FormItem>

      <template v-if="setting.conditionType === ConditionType.RULE">
        <FormItem>
          <template #label>
            满足以下条件（任一分支设为「默认」可兜底）
          </template>
          <div class="rule-logic">
            <span>条件组合方式：</span>
            <RadioGroup v-model:value="groups.and" size="small" button-style="solid">
              <RadioButton :value="true">且</RadioButton>
              <RadioButton :value="false">或</RadioButton>
            </RadioGroup>
          </div>
          <div v-for="(rule, idx) in firstCondition.rules" :key="idx" class="rule-row">
            <Select
              v-model:value="rule.leftSide"
              :options="ALERT_VARIABLE_FIELDS"
              placeholder="告警字段"
              style="flex: 1.4"
              show-search
              option-filter-prop="label"
            />
            <Select v-model:value="rule.opCode" :options="COMPARISON_OPERATORS" style="flex: 1" />
            <Input v-model:value="rule.rightSide" placeholder="值" style="flex: 1" />
            <Button type="text" danger size="small" @click="removeRule(idx)">
              <Icon icon="ant-design:delete-outlined" />
            </Button>
            <span v-if="idx < firstCondition.rules.length - 1" class="rule-join">{{ andLabel }}</span>
          </div>
          <Button type="dashed" block @click="addRule">
            <Icon icon="ant-design:plus-outlined" /> 添加条件
          </Button>
        </FormItem>
      </template>

      <template v-else>
        <FormItem label="条件表达式（Flowable EL）">
          <Input.TextArea
            v-model:value="setting.conditionExpression"
            :rows="3"
            placeholder="${alertEvent == 'intrusion'}"
          />
        </FormItem>
      </template>

      <Divider />
      <FormItem>
        <div class="default-flow">
          <div>
            <div>默认分支</div>
            <div class="default-flow__tip">
              开启后其它条件都不命中时走该分支（同一分支组内建议只设一个）
            </div>
          </div>
          <Switch v-model:checked="setting.defaultFlow" />
        </div>
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

.rule-logic {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
}

.rule-row {
  position: relative;
  display: flex;
  gap: 6px;
  align-items: center;
  padding-right: 4px;
  margin-bottom: 8px;
}

.rule-join {
  position: absolute;
  right: -4px;
  bottom: -16px;
  z-index: 1;
  color: #0a7cff;
  font-size: 12px;
}

.default-flow {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.default-flow__tip {
  color: #8c94a5;
  font-size: 12px;
}
</style>
