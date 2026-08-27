import type {FormSchema} from '@/components/Form';

// APP面板 卡片视图搜索表单（与表格视图一致的查询条件）
export const getFormConfig = (): FormSchema[] => {
  return [
    {
      field: 'templateName',
      label: '模板名称',
      component: 'Input',
      componentProps: {
        placeholder: '请输入模板名称',
      },
    },
    {
      field: 'productIdentification',
      label: '绑定产品',
      component: 'Select',
      componentProps: {
        showSearch: true,
        optionFilterProp: 'label',
        allowClear: true,
        placeholder: '全部产品',
        options: [] as any[],
      },
    },
    {
      field: 'status',
      label: '状态',
      component: 'Select',
      componentProps: {
        allowClear: true,
        placeholder: '全部状态',
        options: [
          {label: '草稿', value: 'DRAFT'},
          {label: '已发布', value: 'PUBLISHED'},
          {label: '已停用', value: 'DISABLED'},
        ],
      },
    },
  ];
};
