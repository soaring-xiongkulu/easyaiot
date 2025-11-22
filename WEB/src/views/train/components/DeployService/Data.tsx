import {BasicColumn, FormProps} from '@/components/Table';

export const getBasicColumns = (): BasicColumn[] => {
  return [
    {
      title: '服务名称',
      dataIndex: 'service_name',
      width: 200,
    },
    {
      title: '模型名称',
      dataIndex: 'model_name',
      width: 150,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
    },
    {
      title: '副本数',
      dataIndex: 'replicas',
      width: 120,
    },
    {
      title: '部署时间',
      dataIndex: 'deploy_time',
      width: 180,
    },
    {
      title: '最后心跳',
      dataIndex: 'last_heartbeat',
      width: 180,
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 250,
      fixed: 'right',
    },
  ];
};

export const getFormConfig = (modelOptions: any[] = []): Partial<FormProps> => {
  return {
    labelWidth: 80,
    baseColProps: {span: 6},
    actionColOptions: {span: 6}, // 按钮占6列，与字段在同一行
    schemas: [
      {
        field: 'model_id',
        label: '模型名称',
        component: 'Select',
        componentProps: {
          placeholder: '请选择模型',
          showSearch: true,
          allowClear: true,
          filterOption: (input: string, option: any) => {
            return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
          },
          options: [
            {label: '全部', value: ''},
            ...modelOptions,
          ],
        },
      },
      {
        field: 'server_ip',
        label: '服务器IP',
        component: 'Input',
        componentProps: {
          placeholder: '请输入服务器IP（模糊查询）',
        },
      },
      {
        field: 'status',
        label: '状态',
        component: 'Select',
        componentProps: {
          placeholder: '请选择状态',
          options: [
            {label: '全部', value: ''},
            {label: '运行中', value: 'running'},
            {label: '已停止', value: 'stopped'},
            {label: '错误', value: 'error'},
          ],
        },
      },
    ],
  };
};

