import {FormProps} from '@/components/Table';
import {BasicColumn} from '@/components/Table/src/types/table';
import {Tag} from "ant-design-vue";

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '设备标识',
      dataIndex: 'deviceIdentification',
      width: 90,
    },
    {
      title: '设备SN',
      dataIndex: 'deviceSn',
      width: 90,
    },
    {
      title: '所属产品',
      dataIndex: 'productName',
      width: 90,
    },
    {
      title: '设备版本',
      dataIndex: 'currentDeviceVersion',
      width: 90,
      customRender: ({text}) => {
        if (text == null) {
          return '1.0.0'
        }
      },
    },
    {
      title: '目标版本',
      dataIndex: 'deviceVersion',
      width: 90,
    },
    {
      width: 60,
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
        field: `deviceIdentification`,
        label: `设备标识`,
        component: 'Input',
      },
      {
        field: `deviceSn`,
        label: `设备SN`,
        component: 'Input',
      },
    ],
  };
}

export function getBatchBasicColumns(): BasicColumn[] {
  return [
    {
      title: '批次号',
      dataIndex: 'batchNumber',
    },
    {
      title: '产品名称',
      dataIndex: 'productName',
    },
    {
      title: '申请数量',
      dataIndex: 'applyAmount',
    },
    {
      title: '成功数量',
      dataIndex: 'successAmount',
    },
    {
      title: '创建时间',
      dataIndex: 'createTime',
    },
    {
      width: 150,
      title: '操作',
      dataIndex: 'action',
    },
  ];
}

export function getBatchFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: {span: 6},
    schemas: [
      {
        field: `batchNumber`,
        label: `批次号`,
        component: 'Input',
      },
    ],
  };
}

export function getBatchDetailBasicColumns(): BasicColumn[] {
  return [
    {
      title: '批次号',
      dataIndex: 'batchNumber',
    },
    {
      title: '设备名称',
      dataIndex: 'deviceName',
    },
    {
      title: '设备标识',
      dataIndex: 'deviceIdentification',
    },
    {
      title: '设备SN',
      dataIndex: 'deviceSn',
    },
    {
      title: '创建状态',
      dataIndex: 'createStatus',
      customRender: ({text}) => {
        return <Tag color={text == 1 ? 'green' : 'red'}>{text == 1 ? '成功' : '失败'}</Tag>;
      },
    },
    {
      width: 400,
      title: '失败原因',
      dataIndex: 'failureCase',
    },
  ];
}

export function getBatchDetailFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: {span: 6},
    schemas: [
      {
        field: `deviceIdentification`,
        label: `设备标识`,
        component: 'Input',
      },
      {
        field: `deviceSn`,
        label: `设备SN`,
        component: 'Input',
      },
      {
        field: `createStatus`,
        label: `创建状态`,
        component: 'Select',
        componentProps: {
          options: createStatusOptions.map((e) => {
            return {
              ...e,
              value: e.key,
            };
          }),
        },
      },
    ],
  };
}

// 功能类型tabs切换
export const createStatusOptions = [
  {
    label: '成功',
    key: '1',
  },
  {
    label: '失败',
    key: '2',
  },
];
