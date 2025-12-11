import { BasicColumn, FormProps } from '@/components/Table';
import { Tag } from 'ant-design-vue';

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '模型名称',
      dataIndex: 'name',
      width: 150,
    },
    {
      title: '服务类型',
      dataIndex: 'service_type',
      width: 100,
      customRender: ({ text }) => {
        const serviceTypeMap: Record<string, string> = {
          online: '线上服务',
          local: '本地服务',
        };
        return serviceTypeMap[text] || text || '线上服务';
      },
    },
    {
      title: '供应商',
      dataIndex: 'vendor',
      width: 100,
      customRender: ({ text }) => {
        const vendorMap: Record<string, string> = {
          aliyun: '阿里云',
          openai: 'OpenAI',
          anthropic: 'Anthropic',
          local: '本地服务',
        };
        return vendorMap[text] || text;
      },
    },
    {
      title: '模型类型',
      dataIndex: 'model_type',
      width: 100,
      customRender: ({ text }) => {
        const typeMap: Record<string, string> = {
          text: '文本',
          vision: '视觉',
          multimodal: '多模态',
        };
        return typeMap[text] || text;
      },
    },
    {
      title: '模型标识',
      dataIndex: 'model_name',
      width: 150,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
    },
    {
      title: '激活状态',
      dataIndex: 'is_active',
      width: 100,
    },
    {
      title: '最后测试时间',
      dataIndex: 'last_test_time',
      width: 180,
    },
    {
      width: 200,
      title: '操作',
      dataIndex: 'action',
    },
  ];
}

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: { span: 6 },
    schemas: [
      {
        field: 'name',
        label: '模型名称',
        component: 'Input',
        componentProps: {
          placeholder: '请输入模型名称',
        },
      },
      {
        field: 'vendor',
        label: '供应商',
        component: 'Select',
        componentProps: {
          placeholder: '请选择供应商',
          options: [
            { label: '全部', value: '' },
            { label: '阿里云', value: 'aliyun' },
            { label: 'OpenAI', value: 'openai' },
            { label: 'Anthropic', value: 'anthropic' },
            { label: '本地服务', value: 'local' },
          ],
        },
      },
      {
        field: 'model_type',
        label: '模型类型',
        component: 'Select',
        componentProps: {
          placeholder: '请选择模型类型',
          options: [
            { label: '全部', value: '' },
            { label: '文本', value: 'text' },
            { label: '视觉', value: 'vision' },
            { label: '多模态', value: 'multimodal' },
          ],
        },
      },
    ],
  };
}
