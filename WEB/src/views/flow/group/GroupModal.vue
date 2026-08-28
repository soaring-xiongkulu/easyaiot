<script lang="ts" setup>
/**
 * 审批用户组新建/编辑弹窗：基础信息 + 成员多选（复用设计器 UserSelectModal）
 */
import { computed, ref, unref } from 'vue'
import { Form, FormItem, Input, Select, Tag } from 'ant-design-vue'
import { BasicModal, useModalInner } from '@/components/Modal'
import { useMessage } from '@/hooks/web/useMessage'
import { createUserGroup, getUserGroup, updateUserGroup } from '@/api/flow/common'
import UserSelectModal from '../components/simple-process-design/modules/UserSelectModal.vue'
import { useCandidateOptions } from '../components/simple-process-design/useCandidateOptions'

defineOptions({ name: 'FlowGroupModal' })

const emit = defineEmits(['success', 'register'])
const { createMessage } = useMessage()
const { users } = useCandidateOptions()
const isUpdate = ref(true)
const currentId = ref<number>()

const formRef = ref()
const form = ref<{ name: string; description: string; memberUserIds: number[]; status: number }>({
  name: '',
  description: '',
  memberUserIds: [],
  status: 0,
})
const memberModalOpen = ref(false)

const selectedUsers = computed(() =>
  users.value.filter(user => form.value.memberUserIds.includes(user.id)),
)

const rules = {
  name: [{ required: true, message: '请输入用户组名称', trigger: 'blur' as const }],
}

const [registerModal, { setModalProps, closeModal }] = useModalInner(async (data) => {
  setModalProps({ confirmLoading: false })
  isUpdate.value = !!data?.isUpdate
  currentId.value = data?.record?.id
  form.value = { name: '', description: '', memberUserIds: [], status: 0 }
  if (unref(isUpdate)) {
    const res = await getUserGroup(data.record.id)
    form.value = {
      name: res.name,
      description: res.description ?? '',
      memberUserIds: [...(res.memberUserIds ?? [])],
      status: res.status ?? 0,
    }
  }
  formRef.value?.clearValidate?.()
})

function handleMembersConfirm(ids: number[]) {
  form.value.memberUserIds = ids
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
    setModalProps({ confirmLoading: true })
    const payload = { ...form.value }
    if (unref(isUpdate))
      await updateUserGroup({ ...payload, id: currentId.value })
    else
      await createUserGroup(payload)

    closeModal()
    emit('success')
    createMessage.success('保存成功')
  }
  finally {
    setModalProps({ confirmLoading: false })
  }
}
</script>

<template>
  <BasicModal v-bind="$attrs" :title="isUpdate ? '编辑用户组' : '新建用户组'" :width="520" @register="registerModal" @ok="handleSubmit">
    <Form ref="formRef" :model="form" :rules="rules" layout="vertical" style="margin-top: 12px">
      <FormItem label="用户组名称" name="name">
        <Input v-model:value="form.name" placeholder="如：安防值班组" :maxlength="30" show-count />
      </FormItem>
      <FormItem label="描述">
        <Input.TextArea v-model:value="form.description" :rows="2" placeholder="用户组用途说明" />
      </FormItem>
      <FormItem label="状态">
        <Select
          v-model:value="form.status"
          :options="[
            { label: '开启', value: 0 },
            { label: '关闭', value: 1 },
          ]"
        />
      </FormItem>
      <FormItem label="组成员">
        <div class="flow-group__members">
          <Tag
            v-for="user in selectedUsers"
            :key="user.id"
            class="flow-group__member-tag"
            closable
            @close="form.memberUserIds = form.memberUserIds.filter(id => id !== user.id)"
          >
            {{ user.nickname }}
          </Tag>
          <a class="flow-group__add" @click="memberModalOpen = true">+ 添加成员</a>
        </div>
      </FormItem>
    </Form>

    <UserSelectModal
      v-model:open="memberModalOpen"
      title="选择组成员"
      :selected-ids="form.memberUserIds"
      @confirm="handleMembersConfirm"
    />
  </BasicModal>
</template>

<style lang="less" scoped>
.flow-group__members {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.flow-group__member-tag {
  margin-right: 0;
}

.flow-group__add {
  color: #0a7cff;
  font-size: 13px;
}
</style>
