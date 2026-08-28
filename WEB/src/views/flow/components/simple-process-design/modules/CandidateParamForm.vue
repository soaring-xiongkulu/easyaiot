<script lang="ts" setup>
/**
 * 候选人参数控件：按策略渲染对应的候选对象选择器，
 * candidateParam 以逗号分隔 ID 存储（与后端 BpmSimpleModelNodeVO 契约一致）。
 */
import { computed, ref } from 'vue'
import { Alert, Button, Select, Tag, TreeSelect } from 'ant-design-vue'
import { CandidateStrategy } from '../consts'
import { buildDeptTree, useCandidateOptions } from '../useCandidateOptions'
import UserSelectModal from './UserSelectModal.vue'

defineOptions({ name: 'FlowCandidateParamForm' })

const props = defineProps<{
  strategy?: CandidateStrategy
  param?: string
  label?: string
}>()

const emit = defineEmits<{
  'update:param': [value: string]
}>()

const { roles, posts, userGroups, depts } = useCandidateOptions()

const userModalOpen = ref(false)

const NEEDS_PARAM = new Set([
  CandidateStrategy.USER,
  CandidateStrategy.ROLE,
  CandidateStrategy.POST,
  CandidateStrategy.DEPT_MEMBER,
  CandidateStrategy.DEPT_LEADER,
  CandidateStrategy.USER_GROUP,
])

const NO_PARAM_TIPS: Partial<Record<CandidateStrategy, string>> = {
  [CandidateStrategy.START_USER_SELECT]: '由发起人在发起流程时自行选择审批人',
  [CandidateStrategy.APPROVE_USER_SELECT]: '由上一节点审批人在审批时选择下一节点审批人',
  [CandidateStrategy.START_USER]: '由流程发起人本人处理',
  [CandidateStrategy.START_USER_DEPT_LEADER]: '自动派给发起人所在部门的负责人',
}

const selectedIds = computed(() =>
  (props.param ?? '').split(',').map(id => Number(id)).filter(id => !Number.isNaN(id) && id > 0),
)

const deptTree = computed(() => buildDeptTree(depts.value))

function setParam(ids: number[]) {
  emit('update:param', ids.join(','))
}

function handleSelectChange(values: (number | string)[]) {
  setParam(values.map(v => Number(v)))
}

function handleUsersConfirm(ids: number[]) {
  setParam(ids)
}
</script>

<template>
  <div class="candidate-param">
    <!-- 指定成员：弹窗选择 -->
    <template v-if="strategy === CandidateStrategy.USER">
      <div class="candidate-param__users">
        <Button preIcon="ant-design:plus-outlined" size="small" @click="userModalOpen = true">
          选择成员
        </Button>
        <div v-if="selectedIds.length" class="candidate-param__tags">
          <Tag
            v-for="id in selectedIds"
            :key="id"
            closable
            @close="setParam(selectedIds.filter(item => item !== id))"
          >
            用户{{ id }}
          </Tag>
        </div>
      </div>
      <UserSelectModal
        v-model:open="userModalOpen"
        :title="label ?? '选择成员'"
        :selected-ids="selectedIds"
        @confirm="handleUsersConfirm"
      />
    </template>

    <!-- 角色 / 岗位 / 用户组：下拉多选 -->
    <Select
      v-else-if="strategy === CandidateStrategy.ROLE"
      mode="multiple"
      allow-clear
      placeholder="请选择角色"
      :value="selectedIds"
      :options="roles.map(item => ({ label: item.name, value: item.id }))"
      :field-names="{ label: 'label', value: 'value' }"
      option-filter-prop="label"
      @change="handleSelectChange"
    />
    <Select
      v-else-if="strategy === CandidateStrategy.POST"
      mode="multiple"
      allow-clear
      placeholder="请选择岗位"
      :value="selectedIds"
      :options="posts.map(item => ({ label: item.name, value: item.id }))"
      option-filter-prop="label"
      @change="handleSelectChange"
    />
    <Select
      v-else-if="strategy === CandidateStrategy.USER_GROUP"
      mode="multiple"
      allow-clear
      placeholder="请选择用户组"
      :value="selectedIds"
      :options="userGroups.map(item => ({ label: item.name, value: item.id }))"
      option-filter-prop="label"
      @change="handleSelectChange"
    />

    <!-- 部门成员 / 部门负责人：部门树多选 -->
    <TreeSelect
      v-else-if="strategy === CandidateStrategy.DEPT_MEMBER || strategy === CandidateStrategy.DEPT_LEADER"
      multiple
      allow-clear
      tree-checkable
      :tree-default-expand-all="false"
      :max-tag-count="3"
      placeholder="请选择部门"
      :value="selectedIds"
      :tree-data="deptTree"
      @change="(values: any) => handleSelectChange(values ?? [])"
    />

    <!-- 无参数策略：提示 -->
    <Alert v-else-if="strategy && NO_PARAM_TIPS[strategy]" :message="NO_PARAM_TIPS[strategy]" type="info" show-icon />
    <Alert v-else-if="strategy && !NEEDS_PARAM.has(strategy)" message="该策略暂未启用" type="warning" show-icon />
  </div>
</template>

<style lang="less" scoped>
.candidate-param {
  width: 100%;
}

.candidate-param__users {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.candidate-param__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>
