// src/views/model/components/modelServiceColumns.ts
import { BasicColumn } from '@/components/Table';
import { Tag } from 'ant-design-vue';

// 模型服务列表列配置
export function getModelServiceColumns(): BasicColumn[] {
  return [
    {
      title: '模型ID',
      dataIndex: 'model_id',
      width: 100,
    },
    {
      title: '模型名称',
      dataIndex: 'model_name',
      width: 150,
    },
    {
      title: '版本',
      dataIndex: 'model_version',
      width: 80,
    },
    {
      title: '存储路径',
      dataIndex: 'minio_model_path',
      width: 200,
      customRender: ({ text }) => {
        if (!text) return '--';
        // 简化长路径显示
        const parts = text.split('/');
        return parts.length > 3
          ? `${parts[0]}/.../${parts.slice(-2).join('/')}`
          : text;
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      customRender: ({ record }) => (
        <Tag color={record.status === 'running' ? 'green' : 'red'}>
          {record.status === 'running' ? '运行中' : '已停止'}
        </Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 120,
      customRender: ({ text }) => {
        if (!text) return '--';
        // 简化日期显示
        return new Date(text).toLocaleDateString();
      }
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 120,
    },
  ];
}

// 搜索表单配置
export function getSearchFormConfig() {
  return {
    schemas: [
      {
        field: 'model_name',
        label: '模型名称',
        component: 'Input',
      },
      {
        field: 'status',
        label: '状态',
        component: 'Select',
        componentProps: {
          options: [
            { label: '全部', value: '' },
            { label: '运行中', value: 'running' },
            { label: '已停止', value: 'stopped' },
          ],
        },
      },
    ],
  };
}
