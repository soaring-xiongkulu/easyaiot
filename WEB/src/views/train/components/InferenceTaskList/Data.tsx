import { BasicColumn } from '@/components/Table';
import { Tag } from 'ant-design-vue';
import dayjs from 'dayjs';

export function getInferenceColumns(): BasicColumn[] {
  return [
    {
      title: '记录ID',
      dataIndex: 'id',
      width: 100,
      fixed: 'left',
    },
    {
      title: '模型名称',
      dataIndex: 'model_name',
      width: 150,
      customRender: ({ text }) => text || '--',
    },
    {
      title: '推理类型',
      dataIndex: 'inference_type',
      width: 100,
      customRender: ({ text }) => {
        const typeMap: Record<string, string> = {
          image: '图片',
          video: '视频',
          rtsp: 'RTSP流',
        };
        return typeMap[text] || text;
      }
    },
    {
      title: '输入源',
      dataIndex: 'input_source',
      width: 200,
      customRender: ({ text }) => {
        if (!text) return '--';
        // 简化长路径/URL显示
        return text.length > 30
          ? `${text.substring(0, 15)}...${text.slice(-10)}`
          : text;
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      customRender: ({ record }) => {
        const statusColor = {
          PROCESSING: 'blue',
          COMPLETED: 'green',
          FAILED: 'red',
          WAITING: 'orange',
        }[record.status];

        const statusText = {
          PROCESSING: '处理中',
          COMPLETED: '已完成',
          FAILED: '失败',
          WAITING: '等待',
        }[record.status] || record.status;

        return <Tag color={statusColor}>{statusText}</Tag>;
      }
    },
    {
      title: '处理帧数',
      dataIndex: 'processed_frames',
      width: 100,
      customRender: ({ text, record }) =>
        record.inference_type === 'video' || record.inference_type === 'rtsp'
          ? text || '0'
          : '--'
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      width: 150,
      customRender: ({ text }) =>
        text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '--'
    },
    {
      title: '处理时长',
      dataIndex: 'processing_time',
      width: 100,
      customRender: ({ text }) =>
        text ? `${parseFloat(text).toFixed(2)}秒` : '--'
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 120,
      fixed: 'right',
    },
  ];
}

export function getInferenceFormConfig() {
  return {
    schemas: [
      {
        field: 'model_id',
        label: '模型ID',
        component: 'Input',
        componentProps: {
          placeholder: '输入模型ID精确查询',
        },
      },
      {
        field: 'inference_type',
        label: '推理类型',
        component: 'Select',
        componentProps: {
          options: [
            { label: '全部', value: '' },
            { label: '图片', value: 'image' },
            { label: '视频', value: 'video' },
            { label: 'RTSP流', value: 'rtsp' },
          ],
        },
      },
      {
        field: 'status',
        label: '状态',
        component: 'Select',
        componentProps: {
          options: [
            { label: '全部', value: '' },
            { label: '处理中', value: 'PROCESSING' },
            { label: '已完成', value: 'COMPLETED' },
            { label: '失败', value: 'FAILED' },
            { label: '等待', value: 'WAITING' },
          ],
        },
      },
      {
        field: 'time_range',
        label: '时间范围',
        component: 'RangePicker',
        componentProps: {
          showTime: true,
          format: 'YYYY-MM-DD HH:mm',
        },
      },
    ],
  };
}
