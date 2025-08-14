<template>
  <div>
    <BasicTable @register="registerTable">
      <template #toolbar>
        <a-button type="primary" @click="openTargetModal()">添加</a-button>
        <PopConfirmButton
          @confirm="deleteAll"
          type="primary"
          color="error"
          placement="topRight"
          :disabled="!checkedKeys.length"
          :title="`小心，确认后，所有选定的规则链将被删除，所有相关的数据将变得不可恢复, 确定要删除${checkedKeys.length}条规则编排吗?`"
          >删除</PopConfirmButton
        >
      </template>
      <template #form-custom>
        <Select
          placeholder="请选择客户"
          v-model:value="scope"
          :options="props.scopeList"
          :disabled="props.scopeList.length <= 1"
        />
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'action'">
          <TableAction
            :stopButtonPropagation="true"
            :actions="[
              {
                icon: 'clarity:note-edit-line',
                onClick: handleEdit.bind(null, record),
              },
              {
                icon: 'ant-design:delete-outlined',

                popConfirm: {
                  placement: 'topRight',
                  title: `确定要删除属性'${record.key}'吗?`,
                  confirm: handleDelete.bind(null, record),
                },
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>
    <BasicModal v-bind="$attrs" @register="registerModal" title="" @ok="handleSubmit">
      <BasicForm @register="registerForm" />
    </BasicModal>
  </div>
</template>
<script lang="ts" setup>
  import { Select } from 'ant-design-vue';
  import { ref, nextTick, watch, watchEffect, defineProps } from 'vue';
  import { BasicTable, useTable, TableAction, BasicColumn, FormProps } from '@/components/Table';
  import {
    getAttribute,
    postPluginsTelemetry,
    deletePluginsTelemetry,
  } from '@/api/device/entity-views';
  import { useMessage } from '@/hooks/web/useMessage';
  import moment from 'moment';
  import { BasicModal, useModal } from '@/components/Modal';
  import { PopConfirmButton } from '@/components/Button';
  import { BasicForm, FormSchema, useForm } from '@/components/Form/index';

  const tplType = ref<string>('add');

  const options = [
    {
      label: '字符串',
      value: 'string',
      key: 'string',
    },
    {
      label: '数字',
      value: 'number',
      key: 'number',
    },
    {
      label: '双精度小数',
      value: 'double',
      key: 'double',
    },
    {
      label: '布尔',
      value: 'boolean',
      key: 'boolean',
    },
    {
      label: 'JSON值',
      value: 'JSON',
      key: 'JSON',
    },
  ];

  const columns: BasicColumn[] = [
    {
      title: '最后更新时间',
      dataIndex: 'lastUpdateTs',
      sorter: true,
    },
    {
      title: '键',
      dataIndex: 'key',
      sorter: true,
      width: 150,
    },
    {
      title: '值',
      dataIndex: 'value',
      ifShow: false,
    },
    {
      title: '值',
      dataIndex: 'valueName',
      width: 150,
    },
  ];
  const schemas: FormSchema[] = [
    {
      field: 'key',
      component: 'Input',
      label: '键',
      colProps: {
        span: 24,
      },
      rules: [
        {
          required: true,
          // @ts-ignore
          validator: async (rule, value) => {
            if (!value) {
              /* eslint-disable-next-line */
              return Promise.reject('值不能为空');
            }
            return Promise.resolve();
          },
          trigger: 'change',
        },
      ],
    },
    {
      field: 'valueType',
      component: 'Select',
      label: '值类型',
      colProps: {
        span: 24,
      },
      defaultValue: 'string',
      componentProps: {
        options: options,
        onChange: handleChange,
        allowClear: false,
      },
    },
    {
      field: 'value',
      component: 'Input',
      label: '字符串',
      colProps: {
        span: 24,
      },
      rules: [
        {
          required: true,
          // @ts-ignore
          validator: async (rule, value) => {
            if (!value) {
              /* eslint-disable-next-line */
              return Promise.reject('值不能为空');
            }
            return Promise.resolve();
          },
          trigger: 'change',
        },
      ],
    },
  ];
  const getFormConfig: Partial<FormProps> = {
    schemas: [
      {
        field: `scope`,
        label: `设备属性范围`,
        labelWidth: 90,
        component: 'Select',
        slot: 'custom',
        colProps: {
          xl: 12,
          xxl: 8,
        },
      },
    ],
  };
  const checkedKeys = ref<Array<string | number>>([]);

  const props = defineProps({
    id: { type: String, default: '' },
    info: { type: Object },
    module: {
      type: String,
      default: 'RULE_CHAIN',
    },
    scopeList: {
      type: Array,
      default: () => {
        return [
          { label: '客户端属性', value: 'CLIENT_SCOPE' },
          { label: '服务端属性', value: 'SERVER_SCOPE' },
          { label: '共享属性', value: 'SHARED_SCOPE' },
        ];
      },
      required: true,
    },
  });
  const { createMessage } = useMessage();

  const [registerModal, { openModal, closeModal, setModalProps }] = useModal();
  const [
    registerForm,
    {
      validateFields,
      resetFields,
      setFieldsValue,
      updateSchema,
      // setProps
    },
  ] = useForm({
    labelWidth: 100,
    schemas,
    showActionButtonGroup: false,
    actionColOptions: {
      span: 24,
    },
  });

  const scope = ref<string>('');
  const tableTitle = ref<string>('');
  watch(
    () => scope.value,
    (newValue) => {
      tableTitle.value = props.scopeList.filter((i) => i.value === newValue)[0].label;
      reload();
    },
  );
  watchEffect(() => {
    scope.value = props.scopeList[0].value;
  });
  const [registerTable, { reload }] = useTable({
    title: tableTitle,
    api: getAttribute,
    beforeFetch: (data) => {
      // 接口请求前 参数处理
      //console.log('-------', data, props);
      let params = {
        module: props.module,
        id: props?.id,
        scope: scope.value,
      };

      return params;
    },
    afterFetch: (data) => {
      //请求之后对返回值进行处理
      //console.log('-------！', data);
      let list = data.map((res, index) => {
        let newDate = new Date(res.lastUpdateTs);
        res.id = index;
        res.lastUpdateTs = moment(newDate)?.format?.('YYYY-MM-DD HH:mm:ss') ?? res.lastUpdateTs;
        res.valueName = res.value + '';
        return res;
      });
      // return list.filter(item => item.key.indexOf('active') > -1)
      return list;
    },
    columns: columns,
    formConfig: getFormConfig,
    useSearchForm: true,
    showIndexColumn: false,
    showTableSetting: false,
    tableSetting: { fullScreen: true },
    rowKey: 'index',
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
    actionColumn: {
      width: 100,
      title: '编辑',
      dataIndex: 'action',
      fixed: 'right',
      // slots: { customRender: 'action' },
    },
  });

  function openTargetModal() {
    tplType.value = 'add';

    setModalProps({ title: '添加属性' });
    openModal(true);
    nextTick(() => {
      updateSchema({
        field: 'key',
        show: true,
      });
      updateSchema({
        field: 'value',
        component: 'Input',
        componentProps: {
          options: [],
        },
        defaultValue: '',
      });
      resetFields();
    });
  }
  function handleEdit(record) {
    tplType.value = 'edit';
    setModalProps({ title: '修改属性' });
    openModal(true);
    let valueType = typeof record.value;
    //console.log(valueType);
    // valueType = valueType === 'number' ? (record.value % 1 === 0 ? 'number' : 'double') : valueType;
    //console.log(record);
    nextTick(() => {
      setFieldsValue({
        key: record.key,
        value: record.value,
        valueType: valueType,
      });
    });
  }

  async function handleDelete(record) {
    let params = {
      keys: record.key,
    };
    await deletePluginsTelemetry('RULE_CHAIN', props?.id, params, 'SERVER_SCOPE');
    reload();
  }
  async function deleteAll() {
    let params = {
      keys: checkedKeys.value.join(','),
    };
    //console.log(checkedKeys);
    try {
      await deletePluginsTelemetry('RULE_CHAIN', props?.id, params, 'SERVER_SCOPE');
      createMessage.success('删除成功');
    }catch (error) {
    console.error(error)
      //console.log(error);
      createMessage.error('删除失败');
    }
    reload();
  }
  function onSelect(record, selected) {
    if (selected) {
      checkedKeys.value = [...checkedKeys.value, record.key];
    } else {
      checkedKeys.value = checkedKeys.value.filter((key) => key !== record.key);
    }
    //console.log(checkedKeys);
  }
  function onSelectAll(selected, _, changeRows) {
    const changeIds = changeRows.map((item) => item.key);
    if (selected) {
      checkedKeys.value = [...checkedKeys.value, ...changeIds];
    } else {
      checkedKeys.value = checkedKeys.value.filter((key) => {
        return !changeIds.includes(key);
      });
    }
    //console.log(checkedKeys);
  }

  async function handleSubmit() {
    try {
      const res = await validateFields();
      const { value, key, valueType } = res;
      let valueSet =
        valueType === 'number' || valueType === 'double'
          ? Number(value)
          : valueType === 'boolean'
          ? Boolean(value)
          : value;

      let params = {
        [key]: valueSet,
      };

      try {
        await postPluginsTelemetry('RULE_CHAIN', props?.id, params, 'SERVER_SCOPE');

        createMessage.success('操作成功');
        reload();
        closeModal();
      }catch (error) {
    console.error(error)
        createMessage.error('操作失败');
      }
    }catch (error) {
    console.error(error)
      //console.log('not passing', error);
    }
  }

  function handleChange(e) {
    //console.log(e);
    // formModel.value = '';
    if (tplType.value === 'add') {
      setFieldsValue({
        value: null,
      });
    } else {
      updateSchema({
        field: 'key',
        show: false,
      });
    }
    let scSet = {};
    if (e === 'boolean') {
      scSet = {
        component: 'RadioGroup',
        componentProps: {
          options: [
            {
              label: '真',
              value: true,
            },
            {
              label: '假',
              value: false,
            },
          ],
        },
        defaultValue: true,
      };
    } else {
      scSet = {
        component: 'Input',
        componentProps: {
          options: [],
        },
        defaultValue: '',
      };
    }
    let label;
    options.forEach((element) => {
      if (element.value === e) {
        label = element.label;
      }
    });
    const defaultSet = {
      field: 'value',
      label: label,
    };
    console.log({
      ...defaultSet,
      ...scSet,
    });
    updateSchema({
      ...defaultSet,
      ...scSet,
    });
  }
</script>
