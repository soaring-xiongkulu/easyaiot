<script lang="ts" setup>
import GroupModal from './GroupModal.vue'
import { columns, searchFormSchema } from './group.data'
import { useI18n } from '@/hooks/web/useI18n'
import { useMessage } from '@/hooks/web/useMessage'
import { useModal } from '@/components/Modal'
import { IconEnum } from '@/enums/appEnum'
import { BasicTable, TableAction, useTable } from '@/components/Table'
import { deleteUserGroup, getUserGroupPage } from '@/api/flow/common'
import { Button } from '@/components/Button'

defineOptions({ name: 'FlowUserGroup' })

const { t } = useI18n()
const { createMessage } = useMessage()
const [registerModal, { openModal }] = useModal()

const [registerTable, { reload }] = useTable({
  title: '审批用户组',
  api: getUserGroupPage,
  columns,
  formConfig: { labelWidth: 100, schemas: searchFormSchema },
  useSearchForm: true,
  showTableSetting: true,
  actionColumn: {
    width: 140,
    title: t('common.action'),
    dataIndex: 'action',
    fixed: 'right',
  },
})

function handleCreate() {
  openModal(true, { isUpdate: false })
}

function handleEdit(record: Recordable) {
  openModal(true, { record, isUpdate: true })
}

async function handleDelete(record: Recordable) {
  await deleteUserGroup(record.id)
  createMessage.success(t('common.delSuccessText'))
  reload()
}
</script>

<template>
  <div>
    <BasicTable @register="registerTable">
      <template #toolbar>
        <Button v-auth="['flow:user-group:create']" type="primary" :preIcon="IconEnum.ADD" @click="handleCreate">
          {{ t('action.create') }}
        </Button>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'memberUserIds'">
          <a-tag color="blue">{{ (record.memberUserIds || []).length }} 人</a-tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <TableAction
            :actions="[
              { icon: IconEnum.EDIT, label: t('action.edit'), auth: 'flow:user-group:update', onClick: handleEdit.bind(null, record) },
              {
                icon: IconEnum.DELETE,
                danger: true,
                label: t('action.delete'),
                auth: 'flow:user-group:delete',
                popConfirm: {
                  title: t('common.delMessage'),
                  placement: 'left',
                  confirm: handleDelete.bind(null, record),
                },
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>
    <GroupModal @register="registerModal" @success="reload()" />
  </div>
</template>
