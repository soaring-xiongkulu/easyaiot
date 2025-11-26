import {FormProps} from '@/components/Table';
import {BasicColumn} from '@/components/Table/src/types/table';
import {Tag} from "ant-design-vue";

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '快捷键编号',
      dataIndex: 'shortcut',
      width: 120,
    },
    {
      title: '标签名称',
      dataIndex: 'name',
      width: 120,
    },
    {
      title: '标签颜色',
      dataIndex: 'color',
      width: 120,
      // 修改点：动态绑定颜色值
      customRender: ({ text }) => {
        // 使用后台返回的text值作为颜色
        return <Tag color={text}>{text}</Tag>;
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      width: 120,
    },
    {
      width: 90,
      title: '操作',
      dataIndex: 'action',
    },
  ];
}

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: {span: 6},
    schemas: [
      {
        field: `shortcut`,
        label: `快捷键编号`,
        component: 'Input',
      },
      {
        field: `name`,
        label: `标签名称`,
        component: 'Input',
      },
    ],
  };
}
