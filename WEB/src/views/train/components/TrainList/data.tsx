// src/views/train/data.tsx
import { BasicColumn } from '@/components/Table';
import { Progress, Tag } from 'ant-design-vue';

// 模型训练表格列配置
export function getTrainTableColumns(): BasicColumn[] {
  return [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      width: 100,
    },
    {
      title: '数据集URL',
      dataIndex: 'dataset_url',
      width: 200,
    },
    {
      title: '模型配置',
      dataIndex: 'model_config',
      width: 150,
      customRender: ({ text }) => {
        return text ? JSON.stringify(text) : '--';
      }
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      width: 120,
    },
    {
      title: '当前状态',
      dataIndex: 'status',
      width: 100,
      customRender: ({ record }) => {
        const statusColorMap = {
          running: 'blue',
          completed: 'green',
          failed: 'red',
          stopped: 'orange'
        };

        const statusTextMap = {
          running: '运行中',
          completed: '已完成',
          failed: '失败',
          stopped: '已停止'
        };

        return (
          <Tag color={statusColorMap[record.status] || 'default'}>
            {statusTextMap[record.status] || record.status}
          </Tag>
        );
      }
    },
    {
      title: '进度',
      dataIndex: 'progress',
      width: 120,
      customRender: ({ record }) => {
        const percent = record.progress || 0;
        const status = record.status === 'running' ? 'active' : 'normal';

        return (
          <Progress
            percent={percent}
            status={status}
            size="small"
          />
        );
      }
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 150,
    },
  ];
}

// 搜索表单配置
export function getSearchFormConfig() {
  return {
    schemas: [
      {
        field: 'status',
        label: '状态',
        component: 'Select',
        componentProps: {
          options: [
            { label: '全部', value: '' },
            { label: '运行中', value: 'running' },
            { label: '已完成', value: 'completed' },
            { label: '失败', value: 'failed' },
            { label: '已停止', value: 'stopped' },
          ],
        },
      },
    ],
  };
}
