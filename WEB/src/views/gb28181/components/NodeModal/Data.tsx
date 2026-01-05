import {BasicColumn, FormProps} from "@/components/Table";
import moment from "moment";

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '分组名称',
      dataIndex: 'groupName',
      width: 240,
    },
    {
      title: '设备标识',
      dataIndex: 'deviceIdentification',
      width: 120,
    },
    {
      title: '设备SN',
      dataIndex: 'deviceSn',
      width: 120,
    },
    {
      title: '产品标识',
      dataIndex: 'productIdentification',
      width: 120,
    },
  ];
}

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: {span: 9},
    schemas: [
      {
        field: `deviceIdentification`,
        label: `设备标识`,
        component: 'Input',
      },
      {
        field: `productIdentification`,
        label: `产品标识`,
        component: 'Input',
      },
    ],
  };
}

export function getGroupBasicColumns(): BasicColumn[] {
  return [
    {
      title: '分组名称',
      dataIndex: 'groupName',
      width: 240,
    },
    {
      title: '产品标识',
      dataIndex: 'productIdentification',
      width: 240,
    },
    {
      width: 110,
      title: '操作',
      dataIndex: 'action',
    },
  ];
}

export function getGroupFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: {span: 9},
    schemas: [
      {
        field: `groupName`,
        label: `分组名称`,
        component: 'Input',
      },
      {
        field: `productIdentification`,
        label: `产品标识`,
        component: 'Input',
      },
    ],
  };
}
