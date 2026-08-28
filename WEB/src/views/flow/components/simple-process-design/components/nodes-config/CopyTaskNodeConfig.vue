<script lang="ts" setup>
/**
 * 抄送人节点配置抽屉：候选人策略 + 参数
 */
import { computed, ref } from 'vue'
import { Drawer, Form, FormItem, Input, Select } from 'ant-design-vue'
import { Icon } from '@/components/Icon'
import type { SimpleFlowNode } from '../../consts'
import { CANDIDATE_STRATEGIES, NODE_VISUALS, NodeType } from '../../consts'
import CandidateParamForm from '../../modules/CandidateParamForm.vue'

defineOptions({ name: 'FlowCopyTaskNodeConfig' })

const props = defineProps<{ node: SimpleFlowNode }>()

const visible = ref(false)

function open() {
  visible.value = true
}

defineExpose({ open })

const node = computed(() => props.node)
const visual = NODE_VISUALS[NodeType.COPY_TASK_NODE]

const strategyOption = computed(() =>
  CANDIDATE_STRATEGIES.find(item => item.value === node.value.candidateStrategy),
)
</script>

<template>
  <Drawer v-model:open="visible" width="560" title="抄送节点配置">
    <div class="config-head">
      <div class="config-head__icon" :style="{ backgroundColor: visual.color }">
        <Icon :icon="visual.icon" />
      </div>
      <Input v-model:value="node.name" placeholder="节点名称" />
    </div>

    <Form layout="vertical">
      <FormItem label="抄送人策略">
        <Select
          v-model:value="node.candidateStrategy"
          placeholder="请选择抄送人策略"
          :options="CANDIDATE_STRATEGIES.map(item => ({ label: item.label, value: item.value }))"
          option-filter-prop="label"
        />
      </FormItem>
      <FormItem v-if="strategyOption?.paramRequired" label="抄送对象">
        <CandidateParamForm
          :strategy="node.candidateStrategy"
          :param="node.candidateParam"
          label="选择抄送人"
          @update:param="(value: string) => (node.candidateParam = value)"
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
