import {BasicColumn, FormProps} from "@/components/Table";
import { Tag } from "ant-design-vue";
import {queryAlertCameras} from "@/api/device/calculate";
import { ALERT_EVENT_OPTIONS, formatAlertEvent, getAlertEventTagColor, getAlertMatchedPersonName, getAlertSourceEvent, formatLlmJudgeStatus, getLlmJudgeStatusColor, isLlmSampled } from "@/views/alert/alertDisplay";

/** 告警列表摄像头筛选：与算法任务里摄像头下拉一致的模糊匹配（按名称） */
export const alertCameraSelectProps = {
  api: queryAlertCameras,
  resultField: 'data',
  labelField: 'label',
  valueField: 'value',
  showSearch: true,
  filterOption: (input: string, option: any) => {
    const q = String(input ?? '').toLowerCase();
    const label = String(option?.label ?? '').toLowerCase();
    const value = String(option?.value ?? '').toLowerCase();
    return label.includes(q) || value.includes(q);
  },
};

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '设备ID',
      dataIndex: 'device_id',
      key: 'device_id',
      width: 120,
    },
    {
      title: '设备名称',
      dataIndex: 'device_name',
      key: 'device_name',
      width: 120,
    },
    {
      title: '告警时间',
      dataIndex: 'time',
      width: 120,
    },
    {
      title: '任务名称',
      dataIndex: 'task_name',
      width: 150,
    },
    {
      title: '告警事件',
      dataIndex: 'event',
      width: 120,
      customRender: ({ text }) => (
        <Tag color={getAlertEventTagColor(text)}>{formatAlertEvent(text)}</Tag>
      ),
    },
    {
      title: '匹配人员',
      dataIndex: 'matched_person_name',
      width: 120,
      customRender: ({ record }) => getAlertMatchedPersonName(record) || '-',
    },
    {
      title: '触发告警',
      dataIndex: 'source_event',
      width: 120,
      customRender: ({ record }) => {
        const sourceEvent = getAlertSourceEvent(record);
        return sourceEvent ? formatAlertEvent(sourceEvent) : '-';
      },
    },
    {
      title: '任务类型',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 100,
      customRender: ({text}) => {
        if (!text) {
          return '实时';
        }
        // 兼容 'snap' 和 'snapshot' 两种值
        if (text === 'snap' || text === 'snapshot') {
          return '抓拍';
        } else if (text === 'realtime') {
          return '实时';
        }
        return text;
      },
    },
    {
      title: '告警对象',
      dataIndex: 'object',
      width: 120,
    },
    {
      title: '业务标签',
      dataIndex: 'business_tags',
      width: 160,
      customRender: ({ text }) => {
        if (!text || !Array.isArray(text) || text.length === 0) {
          return '-';
        }
        return (
          <span>
            {text.map((tag: string) => (
              <Tag key={tag} color="blue" style={{ marginRight: '4px', marginBottom: '4px' }}>
                {tag}
              </Tag>
            ))}
          </span>
        );
      },
    },
    {
      title: '检测区域',
      dataIndex: 'region',
      width: 120,
      customRender: ({text}) => {
        if (text === null) {
          return '不限区域';
        }
        return text;
      },
    },
    {
      title: 'AI研判',
      dataIndex: 'llm_judge_status',
      width: 110,
      customRender: ({ record }) => {
        const status: string | undefined = record?.llm_judge_status;
        // 未命中抽检的告警不显示 AI 标签，仅被抽检的告警展示
        if (!isLlmSampled(status)) {
          return '-';
        }
        return <Tag color={getLlmJudgeStatusColor(status)}>{formatLlmJudgeStatus(status)}</Tag>;
      },
    },
    {
      width: 120,
      title: '操作',
      dataIndex: 'action',
    },
  ];
}

/** 告警筛选：重置/查询占第三列，与上方表单项对齐 */
export const alertFilterActionColOptions = {
  span: 8,
  style: {
    textAlign: 'left' as const,
    paddingLeft: '120px',
    boxSizing: 'border-box' as const,
  },
};

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 120,
    baseColProps: {span: 8},
    actionColOptions: alertFilterActionColOptions,
    showAdvancedButton: false,
    alwaysShowLines: 2,
    schemas: [
      {
        field: 'task_name',
        label: '任务名称',
        component: 'Input',
        componentProps: {
          placeholder: '请输入任务名称（支持模糊匹配）',
        },
        colProps: {span: 8},
      },
      {
        field: `device_id`,
        label: `摄像头`,
        component: 'ApiSelect',
        componentProps: alertCameraSelectProps,
        defaultValue: '',
        colProps: {span: 8},
      },
      {
        field: `event`,
        label: `告警事件`,
        component: 'Select',
        componentProps: {
          options: [...ALERT_EVENT_OPTIONS],
        },
        colProps: {span: 8},
      },
      {
        field: 'llm_judge_status',
        label: 'AI抽检',
        component: 'Select',
        helpMessage: '已抽检含确认成立/误报/研判中/研判失败全部被 AI 抽检的告警，未抽检为未命中抽检',
        componentProps: {
          options: [
            { label: '全部', value: '' },
            { label: '未抽检', value: 'not_sampled' },
            { label: '已抽检', value: 'confirmed,rejected,pending,error' },
            { label: '确认成立', value: 'confirmed' },
            { label: '误报', value: 'rejected' },
            { label: '研判中', value: 'pending' },
            { label: '研判失败', value: 'error' },
          ],
          placeholder: '全部',
        },
        colProps: {span: 8},
      },
      {
        field: '[begin_datetime, end_datetime]',
        label: '告警时间',
        component: 'RangePicker',
        componentProps: {
          format: 'YYYY-MM-DD HH:mm:ss',
          placeholder: ['开始时间', '结束时间'],
          showTime: { format: 'HH:mm:ss' },
        },
        colProps: {span: 8},
      },
    ]
  }
}

/** 窄栏内下拉/日期面板挂到 body，避免被 overflow 裁切 */
function withMapPopupContainer<T extends { component?: string; componentProps?: Record<string, unknown> | ((...args: unknown[]) => unknown) }>(
  schema: T,
): T {
  const popupComponents = new Set(['ApiSelect', 'Select', 'RangePicker']);
  if (!schema.component || !popupComponents.has(schema.component)) {
    return schema;
  }
  if (typeof schema.componentProps === 'function') {
    return schema;
  }
  return {
    ...schema,
    componentProps: {
      ...(schema.componentProps || {}),
      getPopupContainer: () => document.body,
    },
  };
}

/** 告警地图弹窗侧栏筛选（窄栏单列，全部条件始终展示） */
export function getAlertMapFilterFormConfig(): Partial<FormProps> {
  const base = getFormConfig();
  const schemaMap = new Map(
    (base.schemas || []).map((schema) => [schema.field as string, schema]),
  );
  const orderedFields = [
    '[begin_datetime, end_datetime]',
    'event',
    'device_id',
    'task_name',
    'llm_judge_status',
  ];
  const schemas = orderedFields
    .map((field) => schemaMap.get(field))
    .filter(Boolean)
    .map((schema) =>
      withMapPopupContainer({
        ...schema!,
        colProps: { span: 24 },
      }),
    );
  return {
    ...base,
    layout: 'vertical',
    labelWidth: 100,
    baseColProps: { span: 24 },
    showActionButtonGroup: false,
    showAdvancedButton: false,
    compact: true,
    colon: false,
    schemas,
  };
}
