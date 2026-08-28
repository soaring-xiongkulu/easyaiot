<script lang="ts" setup>
/**
 * 流程分类管理（标准 CRUD，对齐 system/post 页面写法）
 */
import { columns, searchFormSchema } from './category.data'
import CategoryModal from './CategoryModal.vue'
import { useI18n } from '@/hooks/web/useI18n'
import { useMessage } from '@/hooks/web/useMessage'
import { useModal } from '@/components/Modal'
import { IconEnum } from '@/enums/appEnum'
import { BasicTable, TableAction, useTable } from '@/components/Table'
import { Button } from '@/components/Button'
import { deleteCategory, getCategoryPage } from '@/api/flow/common'

defineOptions({ name: 'FlowCategory' })

const { t } = useI18n()
const { createMessage } = useMessage()
const [registerModal, { openModal }] = useModal()

const [registerTable, { reload }] = useTable({
  title: '流程分类',
  api: getCategoryPage,
  columns,
  formConfig: { labelWidth: 100, schemas: searchFormSchema },
  useSearchForm: true,
  showTableSetting: true,
  actionColumn: { width: 140, title: t('common.action'), dataIndex: 'action', fixed: 'right' },
})

function handleCreate() {
  openModal(true, { isUpdate: false })
}

function handleEdit(record: Recordable) {
  openModal(true, { record, isUpdate: true })
}

async function handleDelete(record: Recordable) {
  await deleteCategory(record.id)
  createMessage.success(t('common.delSuccessText'))
  reload()
}
</script>

<template>
  <div>
    <BasicTable @register="registerTable">
      <template #toolbar>
        <Button v-auth="['flow:category:create']" type="primary" :preIcon="IconEnum.ADD" @click="handleCreate">
          {{ t('action.create') }}
        </Button>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'action'">
          <TableAction
            :actions="[
              { icon: IconEnum.EDIT, label: t('action.edit'), auth: 'flow:category:update', onClick: handleEdit.bind(null, record) },
              {
                icon: IconEnum.DELETE,
                danger: true,
                label: t('action.delete'),
                auth: 'flow:category:delete',
                popConfirm: { title: t('common.delMessage'), placement: 'left', confirm: handleDelete.bind(null, record) },
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>
    <CategoryModal @register="registerModal" @success="reload()" />
  </div>
</template>
