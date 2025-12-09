// 推流转发任务表格列定义
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
      title: '输出格式',
      dataIndex: 'output_format',
      width: 100,
      customRender: ({ text }) => {
        return (
          <Tag color={text === 'rtmp' ? 'blue' : 'green'}>
            {text?.toUpperCase() || 'RTMP'}
          </Tag>
        );
      },
    },
    {
      title: '输出质量',
      dataIndex: 'output_quality',
      width: 100,
      customRender: ({ text }) => {
        const colorMap: Record<string, string> = {
          'low': 'default',
          'medium': 'orange',
          'high': 'green',
        };
        const textMap: Record<string, string> = {
          'low': '低',
          'medium': '中',
          'high': '高',
        };
        return (
          <Tag color={colorMap[text] || 'default'}>
            {textMap[text] || text}
          </Tag>
        );
      },
    },
    {
      title: '运行状态',
      dataIndex: 'is_enabled',
      width: 100,
      customRender: ({ text }) => {
        return (
          <Tag color={text ? 'green' : 'default'}>
            {text ? '运行中' : '已停止'}
          </Tag>
        );
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
    labelWidth: 100,
    schemas: [
      {
        field: 'search',
        label: '搜索',
        component: 'Input',
        componentProps: {
          placeholder: '请输入任务名称或编号',
          allowClear: true,
        },
      },
      {
        field: 'is_enabled',
        label: '运行状态',
        component: 'Select',
        componentProps: {
          placeholder: '请选择运行状态',
          allowClear: true,
          options: [
            { label: '运行中', value: 1 },
            { label: '已停止', value: 0 },
          ],
        },
      },
    ],
  };
}

