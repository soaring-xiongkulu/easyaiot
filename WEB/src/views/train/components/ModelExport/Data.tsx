import {BasicColumn, FormProps} from "@/components/Table";

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '导出ID',
      dataIndex: 'id',
      width: 90,
    },
    {
      title: '模型ID',
      dataIndex: 'model_id',
      width: 100,
      align: 'center',
    },
    {
      title: '模型名称',
      dataIndex: 'model_name',
      width: 150,
      customRender: ({record}) => {
        const modelName = record.model_name || `模型${record.model_id}`;
        const version = record.model_version;
        return version ? `${modelName}（v${version}）` : modelName;
      },
    },
    {
      title: '导出格式',
      dataIndex: 'format',
      width: 120,
      align: 'center',
      customRender: ({text}) => {
        const formatMap: Record<string, string> = {
          'onnx': 'ONNX',
          'openvino': 'OpenVINO',
        };
        return formatMap[text] || text?.toUpperCase() || '--';
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 120,
      align: 'center',
      customRender: ({text}) => {
        const statusMap: Record<string, {text: string; color: string}> = {
          'PENDING': {text: '等待中', color: 'default'},
          'PROCESSING': {text: '处理中', color: 'processing'},
          'COMPLETED': {text: '已完成', color: 'success'},
          'FAILED': {text: '失败', color: 'error'},
        };
        const status = statusMap[text] || {text: text || '--', color: 'default'};
        return status.text;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      align: 'center',
      customRender: ({text}) => formatDateTime(text),
    },
    {
      width: 150,
      title: '操作',
      dataIndex: 'action',
      fixed: 'right',
    },
  ];
}

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: {span: 6},
    actionColOptions: {span: 6}, // 按钮占6列，与字段在同一行
    schemas: [
      {
        field: `model_name`,
        label: `模型名称`,
        component: 'Input',
        componentProps: {
          placeholder: '请输入模型名称',
          allowClear: true,
        },
      },
      {
        field: `status`,
        label: `状态`,
        component: 'Select',
        componentProps: {
          placeholder: '请选择状态',
          allowClear: true,
          options: [
            {label: '等待中', value: 'PENDING'},
            {label: '处理中', value: 'PROCESSING'},
            {label: '已完成', value: 'COMPLETED'},
            {label: '失败', value: 'FAILED'},
          ],
        },
      },
    ],
  };
}

function formatDateTime(dateString: string): string {
  if (!dateString) return '--';
  try {
    // 解析ISO格式时间字符串（可能包含时区信息）
    const date = new Date(dateString);
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      return dateString;
    }
    return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', {hour12: false});
  } catch (e) {
    return dateString;
  }
}

