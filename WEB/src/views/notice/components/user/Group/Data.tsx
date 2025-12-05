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
          5: 'Webhook',
          6: '钉钉',
          7: '飞书',
        }[text];
      },
    },
    {
      title: '名称',
      dataIndex: 'userGroupName',
    },
    {
      title: '用户',
      dataIndex: 'tpreviewUsers',
      ellipsis: true,
      customRender: ({ value }) => {
        const tpreviewUsers = value || [];
        const str = tpreviewUsers.reduce((p, c) => {
          p += c.previewUser + ',';
          return p;
        }, '');
        return str.slice(0, str.length - 1);
      },
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
            { label: '钉钉', value: 6 },
          ],
        },
        defaultValue: 3,
      },
      {
        field: `userGroupName`,
        label: `名称`,
        component: 'Input',
      },
    ],
  };
};

export const formSchemas = ({ changeMsgType }): FormSchema[] => {
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
      field: 'userGroupName',
      component: 'Input',
      label: '名称',
      required: true,
      colProps: {
        span: 11,
      },
    },
    {
      field: 'msgType',
      label: '类型',
      required: true,
      component: 'Select',
      colProps: {
        span: 11,
        push: 2,
      },
      componentProps: {
        options: [
          { label: '阿里云短信', value: 1 },
          { label: '腾讯云短信', value: 2 },
          { label: 'EMail', value: 3 },
          { label: '企业微信', value: 4 },
          { label: '钉钉', value: 6 },
        ],
        onChange: (ev) => {
          changeMsgType(ev);
        },
      },
      defaultValue: 3,
    },
  ];
};
// 新增用户
export const getPreviewUserColumns = (): BasicColumn[] => {
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
          5: 'Webhook',
          6: '钉钉',
          7: '飞书',
        }[text];
      },
    },
    {
      title: '用户',
      dataIndex: 'previewUser',
    },
  ];
};
