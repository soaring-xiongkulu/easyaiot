<script lang="ts" setup>
/**
 * 条件（分支列头）配置抽屉：条件规则（告警变量 + 运算符 + 值）/ 条件表达式 / 默认分支
 * 数据落在 conditionSetting，规则结构与后端 ConditionGroups 契约一致。
 */
import { computed, ref } from 'vue'
import { Button, Divider, Drawer, Input, RadioButton, RadioGroup, Select, Switch } from 'ant-design-vue'
import { Icon } from '@/components/Icon'
import type { SimpleFlowNode } from '../../consts'
import { ALERT_VARIABLE_FIELDS, COMPARISON_OPERATORS, ConditionType, CONDITION_CONFIG_TYPES, NODE_VISUALS, NodeType } from '../../consts'

defineOptions({ name: 'FlowConditionNodeConfig' })

const props = defineProps<{
  node: SimpleFlowNode
  /** 当前分支在分支组内的优先级（从 1 开始），并行分支不传 */
  priority?: number
}>()

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

const isDefault = computed(() => !!setting.value.defaultFlow)

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
  <Drawer v-model:open="visible" width="600" title="分支条件配置">
    <!-- 头部：图标 + 名称 + 优先级 -->
    <div class="cfg-head">
      <div class="cfg-head__icon" :style="{ background: `linear-gradient(135deg, ${visual.color} 0%, #f7b955 100%)` }">
        <Icon :icon="visual.icon" />
      </div>
      <div class="cfg-head__body">
        <Input v-model:value="node.name" placeholder="分支名称（如：夜间入侵）" size="large" />
        <span v-if="!isDefault && priority" class="cfg-head__pri">优先级 {{ priority }}</span>
        <span v-else-if="isDefault" class="cfg-head__pri cfg-head__pri--default">默认分支</span>
      </div>
    </div>

    <div class="cfg-body">
      <!-- 条件类型 -->
      <div class="cfg-card">
        <div class="cfg-card__head">
          <span class="cfg-card__title">条件类型</span>
          <span class="cfg-card__desc">按告警字段规则匹配，或直接编写表达式</span>
        </div>
        <RadioGroup v-model:value="setting.conditionType" button-style="solid" class="cfg-type" @change="handleTypeChange">
          <RadioButton v-for="item in CONDITION_CONFIG_TYPES" :key="item.value" :value="item.value" class="cfg-type__item">
            {{ item.label }}
          </RadioButton>
        </RadioGroup>
      </div>

      <!-- 条件规则 -->
      <div v-if="setting.conditionType === ConditionType.RULE" class="cfg-card">
        <div class="cfg-card__head">
          <span class="cfg-card__title">条件规则</span>
          <div class="cfg-logic">
            <span class="cfg-logic__label">组合方式</span>
            <RadioGroup v-model:value="groups.and" size="small" button-style="solid">
              <RadioButton :value="true">且</RadioButton>
              <RadioButton :value="false">或</RadioButton>
            </RadioGroup>
          </div>
        </div>
        <div class="cfg-rules">
          <div v-for="(rule, idx) in firstCondition.rules" :key="idx" class="cfg-rule">
            <div class="cfg-rule__row">
              <Select
                v-model:value="rule.leftSide"
                :options="ALERT_VARIABLE_FIELDS"
                placeholder="告警字段"
                style="flex: 1.5"
                show-search
                option-filter-prop="label"
              />
              <Select v-model:value="rule.opCode" :options="COMPARISON_OPERATORS" style="flex: 0.9" />
              <Input v-model:value="rule.rightSide" placeholder="值" style="flex: 1" />
              <Button v-if="firstCondition.rules.length > 1" type="text" danger class="cfg-rule__del" @click="removeRule(idx)">
                <Icon icon="ant-design:delete-outlined" />
              </Button>
            </div>
            <span v-if="idx < firstCondition.rules.length - 1" class="cfg-rule__join">{{ andLabel }}</span>
          </div>
          <Button type="dashed" block class="cfg-rules__add" @click="addRule">
            <Icon icon="ant-design:plus-outlined" /> 添加条件
          </Button>
        </div>
      </div>

      <!-- 条件表达式 -->
      <div v-else class="cfg-card">
        <div class="cfg-card__head">
          <span class="cfg-card__title">条件表达式</span>
          <span class="cfg-card__desc">Flowable EL 语法</span>
        </div>
        <Input.TextArea
          v-model:value="setting.conditionExpression"
          :rows="4"
          class="cfg-expression"
          placeholder="${alertEvent == 'intrusion'}"
        />
      </div>

      <!-- 默认分支 -->
      <div class="cfg-card">
        <div class="cfg-default">
          <div class="cfg-default__icon">
            <Icon icon="ant-design:vertical-align-bottom-outlined" />
          </div>
          <div class="cfg-default__body">
            <div class="cfg-default__title">默认分支</div>
            <div class="cfg-default__desc">
              开启后，其它条件都不命中时走该分支（同一分支组内建议只设一个）
            </div>
          </div>
          <Switch v-model:checked="setting.defaultFlow" />
        </div>
      </div>

      <Divider class="cfg-divider" />
      <div class="cfg-tip">
        <Icon icon="ant-design:info-circle-outlined" style="margin-right: 6px" />
        分支从上到下按优先级依次匹配，命中即执行该分支
      </div>
    </div>
  </Drawer>
</template>

<style scoped>
/* ---------- 头部 ---------- */
.cfg-head {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 4px 0 20px;
}

.cfg-head__icon {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  color: #fff;
  font-size: 18px;
  flex-shrink: 0;
  box-shadow: 0 4px 10px rgb(245 166 35 / 30%);
}

.cfg-head__body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.cfg-head__pri {
  width: fit-content;
  padding: 0 8px;
  border-radius: 4px;
  background: #f0f5ff;
  color: #0a7cff;
  font-size: 11px;
  line-height: 18px;
}

.cfg-head__pri--default {
  background: #f6ffed;
  color: #52c41a;
}

/* ---------- 画布与分区卡 ---------- */
.cfg-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  background: #f5f7fa;
}

.cfg-card {
  padding: 14px 16px 16px;
  border: 1px solid #eef0f4;
  border-radius: 10px;
  background: #fff;
}

.cfg-card__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.cfg-card__title {
  color: #1f2d3d;
  font-size: 13px;
  font-weight: 600;
}

.cfg-card__desc {
  color: #8c94a5;
  font-size: 12px;
}

/* ---------- 条件类型 ---------- */
.cfg-type {
  display: flex;
  width: 100%;
}

.cfg-type :deep(.ant-radio-button-wrapper) {
  flex: 1;
  text-align: center;
}

/* ---------- 条件规则 ---------- */
.cfg-logic {
  display: flex;
  gap: 8px;
  align-items: center;
}

.cfg-logic__label {
  color: #8c94a5;
  font-size: 12px;
}

.cfg-rules {
  padding: 12px;
  border-radius: 8px;
  background: #f7f9fc;
}

.cfg-rule {
  position: relative;
}

.cfg-rule__row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.cfg-rule__del {
  flex-shrink: 0;
}

.cfg-rule__join {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 24px;
  height: 20px;
  margin: 4px auto;
  border: 1px solid #d6e4ff;
  border-radius: 10px;
  background: #fff;
  color: #0a7cff;
  font-size: 12px;
  line-height: 1;
}

.cfg-rules__add {
  margin-top: 4px;
  color: #0a7cff;
  border-color: #d6e4ff;
  background: #fff;
}

.cfg-rules__add:hover {
  border-color: #0a7cff;
  color: #0a7cff;
  background: #f0f5ff;
}

/* ---------- 条件表达式 ---------- */
.cfg-expression :deep(textarea) {
  background: #f7f9fc;
}

/* ---------- 默认分支 ---------- */
.cfg-default {
  display: flex;
  gap: 12px;
  align-items: center;
}

.cfg-default__icon {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #f6ffed;
  color: #52c41a;
  font-size: 16px;
  flex-shrink: 0;
}

.cfg-default__body {
  flex: 1;
}

.cfg-default__title {
  color: #1f2d3d;
  font-size: 13px;
  font-weight: 500;
}

.cfg-default__desc {
  margin-top: 2px;
  color: #8c94a5;
  font-size: 12px;
  line-height: 18px;
}

/* ---------- 底部提示 ---------- */
.cfg-divider {
  margin: 4px 0;
}

.cfg-tip {
  display: flex;
  align-items: center;
  color: #8c94a5;
  font-size: 12px;
}
</style>
