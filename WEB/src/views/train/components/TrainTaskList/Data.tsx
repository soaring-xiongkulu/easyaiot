import {BasicColumn, FormProps} from '@/components/Table';
import {Progress, Tag} from 'ant-design-vue';
import {formatClusterRuntime, formatSchedulePolicy} from '@/utils/clusterRuntime';
import {formatTrainProgressDetail, formatTrainTaskTime} from './trainTaskUtils';

const getProgressColor = (percent) => {
  const lightness = 45 + (percent / 100) * 30;
  return `hsl(120, 80%, ${lightness}%)`;
};

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '任务名称',
      dataIndex: 'name',
      width: 160,
    },
    {
      title: '数据集',
      dataIndex: 'dataset_name',
      width: 220,
      customRender: ({ record }) => {
        const name = record.dataset_name;
        const version = record.dataset_version;
        if (name && version) return `${name}（${version}）`;
        if (name) return name;
        if (version) return version;
        return '--';
      },
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      width: 120,
      responsive: ['md'],
      customRender: ({text}) => formatTrainTaskTime(text),
    },
    {
      title: '训练进度',
      dataIndex: 'progress',
      width: 220,
      align: 'center',
      customRender: ({ record }) => {
        const progress = record.progress || 0;
        const detail = formatTrainProgressDetail(record);
        return (
          <div class="w-full">
            <div class="flex items-center w-full gap-2">
              <div class="flex-1">
                <Progress
                  percent={progress}
                  strokeColor={getProgressColor(progress)}
                  strokeWidth={12}
                  strokeLinecap="butt"
                  showInfo={false}
                  class="dynamic-progress"
                />
              </div>
              <div class="text-black font-medium min-w-[40px] text-right">
                {progress}%
              </div>
            </div>
            {detail && <div class="text-xs text-gray-500 mt-1 text-left">{detail}</div>}
          </div>
        );
      },
    },
    {
      title: '调度策略',
      dataIndex: 'schedule_policy',
      width: 110,
      responsive: ['lg'],
      customRender: ({ text, record }) => formatSchedulePolicy(text, record),
    },
    {
      title: '运行节点',
      dataIndex: 'service_server_ip',
      width: 180,
      responsive: ['lg'],
      customRender: ({ record }) => formatClusterRuntime(record),
    },
    {
      title: '当前状态',
      dataIndex: 'status',
      width: 90,
      customRender: ({ record }) => {
        const statusConfig = {
          idle: { color: '#d9d9d9', text: '等待开始', icon: 'clock-circle' },
          preparing: { color: '#13c2c2', text: '准备中', icon: 'loading' },
          Train: { color: '#52c41a', text: `训练中 (${record.progress || 0}%)`, icon: 'sync' },
          train: { color: '#52c41a', text: `训练中 (${record.progress || 0}%)`, icon: 'sync' },
          running: { color: '#52c41a', text: `训练中 (${record.progress || 0}%)`, icon: 'sync' },
          completed: { color: '#1890ff', text: '已完成', icon: 'check-circle' },
          stopped: {
            color: record.can_resume ? '#722ed1' : '#8c8c8c',
            text: record.can_resume ? '已停止(可续训)' : '已停止',
            icon: 'pause-circle',
          },
          stopping: { color: '#8c8c8c', text: '停止中', icon: 'pause-circle' },
          error: {
            color: '#f5222d',
            text: record.can_resume ? '失败(可续训)' : '失败',
            icon: 'close-circle',
          },
          failed: {
            color: '#f5222d',
            text: record.can_resume ? '失败(可续训)' : '失败',
            icon: 'close-circle',
          },
        };

        const config = statusConfig[record.status] || {
          color: 'default',
          text: record.status,
          icon: 'question-circle',
        };

        return (
          <div class="items-center">
            <a-icon type={config.icon} style={{ color: config.color }} />
            <Tag color={config.color}>
              {config.text}
            </Tag>
          </div>
        );
      },
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 180,
    },
  ];
}

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: {span: 6},
    schemas: [
      {
        field: 'task_name',
        label: '任务名称',
        component: 'Input',
      },
      {
        field: 'progress_filter',
        label: '训练进度',
        component: 'Select',
        componentProps: {
          options: [
            {label: '全部', value: ''},
            {label: '未开始 (0%)', value: 'not_started'},
            {label: '进行中 (1-99%)', value: 'in_progress'},
            {label: '已完成 (100%)', value: 'completed'},
          ],
        },
      },
    ],
  };
}
