import {BasicColumn, FormProps} from "@/components/Table";

export function getOnvifBasicColumns(): BasicColumn[] {
  return [
    {
      title: 'IP地址',
      dataIndex: 'ip',
      width: 60,
    },
    {
      title: 'MAC地址',
      dataIndex: 'mac',
      width: 60,
    },
    {
      title: '设备型号',
      dataIndex: 'hardware_name',
      width: 90,
    },
    {
      title: '操作',
      dataIndex: 'operation',
      width: 120,
      fixed: 'right',
    }
  ];
}

export function getOnvifFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: {span: 11},
    schemas: [
      {
        field: `ip`,
        label: `IP地址`,
        component: 'Input',
      },
      {
        field: `mac`,
        label: `MAC地址`,
        component: 'Input',
      },
    ]
  }
}
