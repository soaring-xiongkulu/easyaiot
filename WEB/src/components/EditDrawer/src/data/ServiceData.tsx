import {FormProps} from '@/components/Table';
import {BasicColumn} from '@/components/Table/src/types/table';
import {Tag} from "ant-design-vue";

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '消息标识',
      dataIndex: 'messageId',
    },
    {
      title: '消息状态',
      dataIndex: 'status',
      customRender: ({text}) => {
        const color = text === 0 ? 'red' : text === 1 ? 'blue' : 'green';
        const content = text === 0 ? '未下发' : text === 1 ? '已下发' : '已回复';
        return <Tag color={color}>{() => content}</Tag>;
      },
    },
    {
      title: '指令名称',
      dataIndex: 'commandName',
    },
    {
      title: '指令标识',
      dataIndex: 'commandCode',
    },
    {
      title: '服务标识',
      dataIndex: 'serviceCode',
    },
    {
      title: '响应时间',
      dataIndex: 'reportTime',
    },
    {
      title: '创建时间',
      dataIndex: 'createTime',
    },
    {
      title: '输入参数',
      dataIndex: 'request',
      defaultHidden: true,
    },
    {
      title: '响应内容',
      dataIndex: 'message',
      defaultHidden: true,
    },
  ];
}

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: {span: 6},
    schemas: [
      {
        field: `status`,
        label: `消息状态`,
        component: 'Select',
        componentProps: {
          options: [
            {value: '', label: '全部'},
            {value: 0, label: '未下发'},
            {value: 1, label: '已下发'},
            {value: 2, label: '已回复'},
          ],
        },
        defaultValue: '',
      },
      {
        field: `serviceCode`,
        label: `服务标识`,
        component: 'Input',
      },
      {
        field: `commandCode`,
        label: `指令标识`,
        component: 'Input',
      },
    ],
  };
}
