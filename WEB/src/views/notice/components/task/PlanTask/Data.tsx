import type { FormProps } from '/@/components/Form';
import { BasicColumn } from '/@/components/Table/src/types/table';
import { formatToDateTime } from '/@/utils/dateUtil';
import { Tooltip } from 'ant-design-vue';

export const getColumns = (): BasicColumn[] => {
  return [
    {
      title: '名称',
      dataIndex: 'msgName',
      width: 220,
    },
    {
      title: '创建时间',
      dataIndex: 'createTime',
      format(val) {
        return val ? formatToDateTime(val) : '-';
      },
      width: 270,
    },
    {
      title: '结果',
      dataIndex: 'result',
      ellipsis: true,
      customRender({ value }) {
        return <Tooltip title={value}>{value}</Tooltip>;
      },
    },
  ];
};

export const getFormConfig = (): FormProps => {
  return {
    labelWidth: 70,
    baseColProps: { span: 6 },
    schemas: [
      {
        field: `name`,
        label: `名称`,
        component: 'Input',
      },
    ],
  };
};

// config
export const formSchemas = () => {
  return [
    {
      field: `type`,
      label: `推送方式`,
      component: 'Select',
      componentProps: {
        options: [
          { label: '在此时间开始推送', value: 'time' },
          { label: '每天固定时间开始推送', value: 'regularTime' },
          { label: '每周固定时间开始推送', value: 'week' },
          { label: '按Cron的表达式触发推送', value: 'cron' },
        ],
        getPopupContainer: () => document.body,
      },
    },
    {
      field: `field1`,
      component: 'DatePicker',
      ifShow: ({ values }) => {
        return values?.type == 'time';
      },
      itemProps: {
        class: 'picker-warpper',
      },
      componentProps: {
        format: 'YYYY-MM-DD HH:mm:ss',
        getPopupContainer: () => document.body,
      },
    },
    {
      field: `field2`,
      component: 'TimePicker',
      ifShow: ({ values }) => {
        return values?.type == 'regularTime';
      },
      itemProps: {
        class: 'picker-warpper',
      },
      componentProps: {
        getPopupContainer: () => document.body,
      },
    },
    {
      field: `field3`,
      component: 'Select',
      ifShow: ({ values }) => {
        return values?.type == 'week';
      },
      colProps: {
        span: 8,
      },
      componentProps: {
        options: [
          { label: '一', value: '' },
          { label: '二', value: '' },
          { label: '三', value: '' },
          { label: '四', value: '' },
          { label: '五', value: '' },
          { label: '六', value: '' },
          { label: '日', value: '' },
        ],
        getPopupContainer: () => document.body,
      },
      itemProps: {
        class: 'week-wapper',
      },
    },
    {
      field: `field4`,
      component: 'TimePicker',
      ifShow: ({ values }) => {
        return values?.type == 'week';
      },
      colProps: {
        span: 16,
      },
      itemProps: {
        class: 'picker-warpper',
      },
      componentProps: {
        getPopupContainer: () => document.body,
      },
    },
    {
      field: `field5`,
      component: 'Input',
      ifShow: ({ values }) => {
        return values?.type == 'cron';
      },
    },
    {
      field: `field6`,
      label: `开始执行时重新导入目标用户`,
      component: 'Checkbox',
      labelWidth: '200px',

      itemProps: {
        class: 'checkbox-warpper',
      },
    },
    {
      field: `field7`,
      component: 'Select',
      required: true,
      componentProps: {
        options: [
          { label: '通过文件导入', value: 'file' },
          { label: '通过SQL导入', value: 'sql' },
        ],
        getPopupContainer: () => document.body,
      },
      rules: [{ required: true, message: '请选择导入方式' }],
      ifShow: ({ values }) => {
        console.log(values);
        return values?.field6;
      },
    },
    {
      field: `field8`,
      label: `将推送结果发送邮件给（回车键确认）`,
      component: 'Checkbox',
      itemProps: {
        class: 'checkbox-warpper',
      },
    },
    {
      field: `field9`,
      component: 'Select',
      required: true,
      componentProps: {
        mode: 'tags',
        placeholder: '请输入邮箱',
        getPopupContainer: () => document.body,
      },
      rules: [{ required: true, message: '请输入邮箱' }],
      ifShow: ({ values }) => {
        return values?.field8;
      },
    },
  ];
};
