// 算法任务表格列定义
import { BasicColumn, FormProps } from "@/components/Table";
import { Tag } from "ant-design-vue";

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '任务名称',
      dataIndex: 'task_name',
      width: 150,
    },
    {
      title: '任务类型',
      dataIndex: 'task_type',
      width: 120,
      customRender: ({ text }) => {
        return (
          <Tag color={text === 'realtime' ? 'blue' : 'green'}>
            {text === 'realtime' ? '实时算法任务' : '抓拍算法任务'}
          </Tag>
        );
      },
    },
    {
      title: '抓拍空间',
      dataIndex: 'space_name',
      width: 120,
      customRender: ({ text }) => {
        return text || '--';
      },
    },
    {
      title: '关联摄像头',
      dataIndex: 'device_names',
      width: 200,
      customRender: ({ text }) => {
        if (!text || !Array.isArray(text) || text.length === 0) {
          return '--';
        }
        return text.join(', ');
      },
    },
    {
      title: '运行状态',
      dataIndex: 'run_status',
      width: 100,
      customRender: ({ text }) => {
        const colorMap: Record<string, string> = {
          running: 'green',
          stopped: 'default',
          restarting: 'orange',
        };
        const textMap: Record<string, string> = {
          running: '运行中',
          stopped: '已停止',
          restarting: '重启中',
        };
        return (
          <Tag color={colorMap[text] || 'default'}>
            {textMap[text] || text}
          </Tag>
        );
      },
    },
    {
      title: '启用状态',
      dataIndex: 'is_enabled',
      width: 100,
      customRender: ({ text }) => {
        return (
          <Tag color={text ? 'green' : 'red'}>
            {text ? '已启用' : '已禁用'}
          </Tag>
        );
      },
    },
    {
      title: '处理帧数',
      dataIndex: 'total_frames',
      width: 100,
      customRender: ({ text }) => {
        return text || 0;
      },
    },
    {
      title: '检测次数',
      dataIndex: 'total_detections',
      width: 100,
      customRender: ({ text }) => {
        return text || 0;
      },
    },
    {
      title: '抓拍次数',
      dataIndex: 'total_captures',
      width: 100,
      customRender: ({ text, record }) => {
        if (record.task_type === 'snap') {
          return text || 0;
        }
        return '--';
      },
    },
    {
      title: '算法服务数',
      dataIndex: 'algorithm_services',
      width: 100,
      customRender: ({ text }) => {
        if (!text || !Array.isArray(text)) {
          return 0;
        }
        return `${text.length} 个`;
      },
    },
    {
      width: 200,
      title: '操作',
      dataIndex: 'action',
      fixed: 'right',
    },
  ];
}

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: { span: 6 },
    // 将按钮放到第一行，与第三个字段同一行
    actionColOptions: {
      span: 6,
      offset: 0,
      style: { textAlign: 'right' }
    },
    schemas: [
      {
        field: 'search',
        label: '任务名称',
        component: 'Input',
        componentProps: {
          placeholder: '请输入任务名称',
        },
      },
      {
        field: 'task_type',
        label: '任务类型',
        component: 'Select',
        componentProps: {
          placeholder: '请选择任务类型',
          options: [
            { value: '', label: '全部' },
            { value: 'realtime', label: '实时算法任务' },
            { value: 'snap', label: '抓拍算法任务' },
          ],
        },
      },
      {
        field: 'is_enabled',
        label: '启用状态',
        component: 'Select',
        componentProps: {
          placeholder: '请选择启用状态',
          options: [
            { value: '', label: '全部' },
            { value: true, label: '已启用' },
            { value: false, label: '已禁用' },
          ],
        },
      },
    ]
  }
}

