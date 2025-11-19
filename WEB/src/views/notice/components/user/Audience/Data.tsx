import { FormSchema } from '/@/components/Form';
import { BasicColumn, FormProps } from '/@/components/Table';

export const getColumns = (): BasicColumn[] => {
  return [
    {
      title: '类型',
      dataIndex: 'msgType',
      customRender: ({ text }) => {
        return {
          1: '阿里云短信',
          2: '腾讯云短信',
          3: 'EMail',
          4: '企业微信',
          5: 'http',
          6: '钉钉',
        }[text];
      },
    },
    {
      title: '用户',
      dataIndex: 'previewUser',
    },
    {
      width: 100,
      title: '操作',
      dataIndex: 'action',
      fixed: 'right',
    },
  ];
};

export const getFormConfig = (): FormProps => {
  return {
    labelWidth: 70,
    baseColProps: { span: 6 },
    schemas: [
      {
        field: `msgType`,
        label: `用户类型`,
        component: 'Select',
        componentProps: {
          options: [
            { label: '阿里云短信', value: 1 },
            { label: '腾讯云短信', value: 2 },
            { label: 'EMail', value: 3 },
            { label: '企业微信', value: 4 },
            // { label: 'http', value: 5 },
            { label: '钉钉', value: 6 },
          ],
        },
        defaultValue: 3,
      },
    ],
  };
};

export const formSchemas = (msgTypeChange): FormSchema[] => {
  return [
    {
      field: 'id',
      component: 'Input',
      colProps: {
        span: 0,
      },
      label: '',
    },
    {
      field: 'msgType',
      label: '类型',
      required: true,
      component: 'Select',
      componentProps: {
        options: [
          { label: '阿里云短信', value: 1 },
          { label: '腾讯云短信', value: 2 },
          { label: 'EMail', value: 3 },
          { label: '企业微信', value: 4 },
          // { label: 'http', value: 5 },
          { label: '钉钉', value: 6 },
        ],
        getPopupContainer: () => document.body,
        onChange: (...ext) => msgTypeChange(...ext),
      },
    },
    {
      field: 'previewUser',
      component: 'Input',
      label: '用户',
      rules: [{ required: true, trigger: ['change', 'blur'] }],
    },
  ];
};
