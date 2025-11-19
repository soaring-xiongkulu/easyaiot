<!-- eslint-disable vue/v-on-event-hyphenation -->
<template>
  <BasicModal
    @register="registerModal"
    @cancel="handleCancel"
    @ok="handleOk"
    :canFullscreen="false"
    wrapClassName="user-group-modal"
    :confirm-loading="loading"
  >
    <BasicForm
      @register="registerForm"
      :showAdvancedButton="false"
      :showActionButtonGroup="false"
    />
    <BasicTable @register="registerTable"/>
  </BasicModal>
</template>
<script lang="ts" setup>
import {nextTick, ref} from 'vue';
import {BasicModal, useModalInner} from '/@/components/Modal';
import {BasicForm, useForm} from '/@/components/Form';
import {useMessage} from '/@/hooks/web/useMessage';
import {formSchemas, getPreviewUserColumns} from '../Data';
import {messagePreviewUserQuery, userGroupAdd, userGroupUpdate} from '/@/api/modules/user';
import {BasicTable, useTable} from '/@/components/Table';

const emits = defineEmits(['success', 'register']);
const {createMessage} = useMessage();
const checkedKeys = ref<Array<string | number>>([]);
const opertionType = ref('add');
const loading = ref(false);
const [registerModal, {setModalProps, closeModal}] = useModalInner((data) => {
  opertionType.value = data.type;
  setModalProps({title: data.type == 'add' ? '新增分组' : '编辑分组'});
  if (data.type == 'edit') {
    editUserConfig(data.record);
  }
});

const [registerForm, {getFieldsValue, validate, setFieldsValue, resetFields}] = useForm({
  schemas: formSchemas({changeMsgType}),
  labelWidth: '100px',
  layout: 'vertical',
  baseColProps: {span: 24},
});

const [registerTable, {reload}] = useTable({
  maxHeight: 240,
  canResize: true,
  showIndexColumn: false,
  title: '用户',
  api: messagePreviewUserQuery,
  beforeFetch: async (params) => {
    await nextTick();
    const {msgType} = getFieldsValue();
    return {
      ...params,
      pageSize: 5,
      msgType,
    };
  },
  columns: getPreviewUserColumns(),
  useSearchForm: false,
  rowKey: 'id',
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  rowSelection: {
    type: 'checkbox',
    selectedRowKeys: checkedKeys,
    onSelect: onSelect,
    onSelectAll: onSelectAll,
  },
});

function onSelect(record, selected) {
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, record.id];
  } else {
    checkedKeys.value = checkedKeys.value.filter((id) => id !== record.id);
  }
}

function onSelectAll(selected, _, changeRows) {
  const changeIds = changeRows.map((item) => item.id);
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, ...changeIds];
  } else {
    checkedKeys.value = checkedKeys.value.filter((id) => {
      return !changeIds.includes(id);
    });
  }
}

function changeMsgType(msgType) {
  resetPreviewUser();
  reload({msgType});
}

function resetPreviewUser() {
  checkedKeys.value = [];
}

function editUserConfig(record) {
  const {id, userGroupName, msgType, previewUserId} = record;
  setFieldsValue({
    id,
    userGroupName,
    msgType,
  });
  setTimeout(() => {
    checkedKeys.value = previewUserId.split(',');
  });
}

const handleCancel = () => {
  resetPreviewUser();
  resetFields();
};

const handleOk = () => {
  validate()
    .then(async () => {
      if (checkedKeys.value.length == 0) {
        createMessage.error('请选择用户');
        return;
      }
      const params = {
        ...getFieldsValue(),
        previewUserId: checkedKeys.value.join(','),
      };
      loading.value = true;
      const ret =
        opertionType.value == 'add' ? await userGroupAdd(params) : await userGroupUpdate(params);
      if (ret.status == 500) {
        createMessage.error(ret.message);
        return;
      }
      closeModal();
      emits('success');
      handleCancel();
      createMessage.success(`${opertionType.value == 'add' ? '新增' : '更新'}成功`);
    })
    .finally(() => {
      loading.value = false;
    })
    .catch(() => {
      createMessage.error(`操作失败`);
    });
};
</script>
<style lang="less" scoped>
:global(.user-group-modal .scrollbar__view > div) {
  height: auto !important;
  min-height: auto !important;
}

:global(.user-group-modal .iot-basic-table-title::before) {
  content: '*';
  margin-right: 5px;
  color: #ff4d4f;
  font-size: 14px;
  font-family: SimSun, sans-serif;
  line-height: 1;
}

:global(.user-group-modal .iot-basic-table-title) {
  padding-left: 0;
  font-size: 14px;
  font-weight: normal;
}

:global(.user-group-modal .ant-table-wrapper) {
  padding: 6px 0;
}
</style>
