<script lang="ts" setup>
/**
 * 发起人节点配置：说明文案 + 发起范围提示（发起权限在模型「基本信息」中配置）
 */
import { ref } from 'vue'
import { Alert, Drawer } from 'ant-design-vue'
import { Icon } from '@/components/Icon'
import type { SimpleFlowNode } from '../../consts'
import { NODE_VISUALS, NodeType } from '../../consts'

defineOptions({ name: 'FlowStartUserNodeConfig' })

defineProps<{ node: SimpleFlowNode }>()

const visible = ref(false)

function open() {
  visible.value = true
}

defineExpose({ open })

const visual = NODE_VISUALS[NodeType.START_USER_NODE]
</script>

<template>
  <Drawer v-model:open="visible" width="520" title="发起人设置">
    <div class="start-user-config__head">
      <div class="start-user-config__icon" :style="{ backgroundColor: visual.color }">
        <Icon :icon="visual.icon" />
      </div>
      <span>{{ node.name }}</span>
    </div>
    <Alert
      type="info"
      show-icon
      message="发起范围"
      description="告警处理流程由告警路由规则按「告警类型 / 设备 / 算法任务」自动发起，发起人为规则配置的系统账号；通用审批流程由用户在审批中心手动发起。发起权限可在模型管理的基本信息中限制。"
    />
  </Drawer>
</template>

<style scoped>
.start-user-config__head {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 600;
}

.start-user-config__icon {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  color: #fff;
}
</style>
