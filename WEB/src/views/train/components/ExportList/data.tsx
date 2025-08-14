// src/views/export/components/exportModelColumns.ts
import { BasicColumn } from '@/components/Table';
import { Tag } from 'ant-design-vue';
import { FormProps } from '@/components/Form';

export function getExportModelColumns(): BasicColumn[] {
  return [
    {
      title: '模型ID',
      dataIndex: 'model_id',
      width: 100,
    },
    {
      title: '原始路径',
      dataIndex: 'model_path',
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
      title: '导出格式',
      dataIndex: 'export_format',
      width: 100,
      customRender: ({ text }) => (
        <Tag>{text?.toUpperCase() || '--'}</Tag>
      )
    },
    {
      title: '导出路径',
      dataIndex: 'export_path',
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
      title: '导出时间',
      dataIndex: 'export_time',
      width: 120,
      customRender: ({ text }) => {
        if (!text) return '--';
        return new Date(text).toLocaleString();
      }
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 120,
    },
  ];
}

// 导出模型搜索表单配置
export function getSearchFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 100,
    baseColProps: { span: 6 },
    schemas: [
      {
        field: 'model_name',
        label: '模型名称',
        component: 'Input',
        componentProps: {
          placeholder: '输入模型名称',
        }
      },
      {
        field: 'export_format',
        label: '导出格式',
        component: 'Select',
        componentProps: {
          placeholder: '选择导出格式',
          options: [
            { label: 'ONNX', value: 'onnx' },
            { label: 'TensorRT', value: 'tensorrt' },
            { label: 'CoreML', value: 'coreml' },
            { label: 'OpenVINO', value: 'openvino' },
          ]
        }
      },
      {
        field: 'date_range',
        label: '导出时间',
        component: 'DatePicker',
        componentProps: {
          type: 'daterange',
          startPlaceholder: '开始日期',
          endPlaceholder: '结束日期',
          valueFormat: 'YYYY-MM-DD',
        }
      }
    ],
  };
}
