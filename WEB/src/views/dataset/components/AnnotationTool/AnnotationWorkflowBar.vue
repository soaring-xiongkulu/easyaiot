<template>
  <div class="workflow-bar">
    <template v-for="(step, idx) in steps" :key="step.key">
      <button
        type="button"
        class="workflow-step"
        :class="stepClass(step)"
        :title="step.hint"
        :disabled="step.disabled"
        @click="emit('action', step.key)"
      >
        <span class="step-dot">
          <Icon v-if="step.status === 'done'" icon="ant-design:check-outlined"/>
          <span v-else class="step-num">{{ step.order }}</span>
        </span>
        <span class="step-label">{{ step.label }}</span>
      </button>
      <span v-if="idx < steps.length - 1" class="step-connector" aria-hidden="true"/>
    </template>
  </div>
</template>

<script setup lang="ts">
import {computed} from 'vue';
import {Icon} from '@/components/Icon';

export type WorkflowStepKey = 'import' | 'annotate' | 'split' | 'sync';

const props = defineProps<{
  totalImages: number;
  completedCount: number;
  usageAllocated: boolean;
  annotationCompleted: boolean;
  syncedToMinio: boolean;
  syncing: boolean;
}>();

const emit = defineEmits<{
  (e: 'action', key: WorkflowStepKey): void;
}>();

type StepStatus = 'pending' | 'active' | 'done';
type WorkflowStep = {
  key: WorkflowStepKey;
  order: number;
  label: string;
  hint: string;
  status: StepStatus;
  disabled: boolean;
};

const currentKey = computed<WorkflowStepKey>(() => {
  if (props.totalImages <= 0) return 'import';
  if (!props.annotationCompleted) return 'annotate';
  if (!props.usageAllocated) return 'split';
  if (!props.syncedToMinio) return 'sync';
  return 'sync';
});

const steps = computed<WorkflowStep[]>(() => {
  const cur = currentKey.value;
  const done = (key: WorkflowStepKey): boolean => {
    if (key === 'import') return props.totalImages > 0;
    if (key === 'annotate') return props.annotationCompleted;
    if (key === 'split') return props.usageAllocated;
    if (key === 'sync') return props.syncedToMinio;
    return false;
  };
  const status = (key: WorkflowStepKey): StepStatus => {
    if (done(key)) return 'done';
    if (key === cur) return 'active';
    return 'pending';
  };

  return [
    {
      key: 'import' as const,
      order: 1,
      label: '导入',
      hint: '添加图片、视频抽帧或从其他格式导入',
      status: status('import'),
      disabled: false,
    },
    {
      key: 'annotate' as const,
      order: 2,
      label: '标注',
      hint:
        props.totalImages > 0
          ? `已完成 ${props.completedCount}/${props.totalImages} 张`
          : '导入图片后开始标注',
      status: status('annotate'),
      disabled: false,
    },
    {
      key: 'split' as const,
      order: 3,
      label: '划分',
      hint: '按比例划分训练/验证/测试集',
      status: status('split'),
      disabled: false,
    },
    {
      key: 'sync' as const,
      order: 4,
      label: props.syncing ? '同步中' : '同步',
      hint: props.syncing ? '同步任务正在执行，请等待完成' : '同步到 Minio 供模型训练使用',
      status: status('sync'),
      disabled: props.syncing,
    },
  ];
});

function stepClass(step: { status: StepStatus; disabled?: boolean }) {
  return {
    'is-done': step.status === 'done',
    'is-active': step.status === 'active',
    'is-pending': step.status === 'pending',
    'is-disabled': !!step.disabled,
  };
}
</script>

<style lang="less" scoped>
@primary: #4361ee;

.workflow-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.workflow-step {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border: 1px solid transparent;
  border-radius: 20px;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  color: #8c8c8c;
  transition: all 0.2s;

  &:hover {
    background: #f5f5f5;
    color: #595959;
  }

  &:disabled,
  &.is-disabled {
    cursor: not-allowed;
    opacity: 0.58;

    &:hover {
      background: transparent;
      color: inherit;
    }
  }

  &.is-active {
    background: fade(@primary, 10%);
    border-color: fade(@primary, 35%);
    color: @primary;
    font-weight: 500;

    .step-dot {
      background: @primary;
      color: #fff;
      border-color: @primary;
    }
  }

  &.is-done {
    color: #52c41a;

    .step-dot {
      background: #f6ffed;
      border-color: #b7eb8f;
      color: #52c41a;
    }
  }

  .step-dot {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    border: 1px solid #d9d9d9;
    font-size: 11px;
    flex-shrink: 0;
  }

  .step-label {
    white-space: nowrap;
  }

  .step-connector {
    width: 16px;
    height: 1px;
    background: #d9d9d9;
    flex-shrink: 0;
  }
}
</style>
