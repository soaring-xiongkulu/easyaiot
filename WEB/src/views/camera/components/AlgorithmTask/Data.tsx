// 算法任务表格列定义
import { BasicColumn, FormProps } from "@/components/Table";
import { Tag } from "ant-design-vue";
import { summarizeMatchingForList } from "@/views/camera/utils/libraryMatching";
import { formatClusterRuntime, formatSchedulePolicy } from '@/utils/clusterRuntime';

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
      width: 160,
      customRender: ({ text, record }) => {
        const executor = String(record?.executor || 'python').toLowerCase();
        const isCpp = executor === 'cpp' || executor === 'c++' || executor === 'runtime';
        const base =
          text === 'realtime' ? '实时视频分析' : text === 'patrol' ? '周期巡检分析' : '事件抓拍分析';
        const label = isCpp ? `${base}（低时延）` : `${base}（全功能）`;
        const color = text === 'realtime' ? 'blue' : text === 'patrol' ? 'purple' : 'green';
        return (
          <Tag color={isCpp ? 'orange' : color}>
            {label}
          </Tag>
        );
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
      title: '调度策略',
      dataIndex: 'schedule_policy',
      width: 110,
      customRender: ({ text, record }) => formatSchedulePolicy(text, record),
    },
    {
      title: '运行节点',
      dataIndex: 'service_server_ip',
      width: 180,
      customRender: ({ record }) => formatClusterRuntime(record),
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
      title: '关联模型',
      dataIndex: 'model_names',
      width: 200,
      customRender: ({ text, record }) => {
        if (text) {
          return text;
        }
        // 如果没有 model_names 但有 model_ids，显示模型数量
        if (record.model_ids && Array.isArray(record.model_ids) && record.model_ids.length > 0) {
          return `已配置 ${record.model_ids.length} 个模型`;
        }
        // 兼容旧数据：显示算法服务
        if (record.algorithm_services && Array.isArray(record.algorithm_services) && record.algorithm_services.length > 0) {
          return record.algorithm_services.map((s: any) => s.service_name).join(', ');
        }
        return '--';
      },
    },
    {
      title: '告警标签',
      dataIndex: 'alert_class_names',
      width: 160,
      customRender: ({ text }) => {
        if (!text || !Array.isArray(text) || text.length === 0) {
          return '--';
        }
        return text.slice(0, 3).map((name: string) => (
          <Tag key={name}>{name}</Tag>
        ));
      },
    },
    {
      title: '库匹配',
      dataIndex: 'matching_business_tags',
      width: 180,
      customRender: ({ record }) => {
        const summary = summarizeMatchingForList(record);
        if (!summary) {
          return '--';
        }
        return (
          <Tag color={summary.mode === 'tags' ? 'green' : 'blue'}>{summary.text}</Tag>
        );
      },
    },
    {
      title: '后处理',
      dataIndex: 'post_process_enabled',
      width: 90,
      customRender: ({ text }) => (
        <Tag color={text ? 'purple' : 'default'}>
          {text ? '已开启' : '未开启'}
        </Tag>
      ),
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
            { value: 'realtime', label: '实时视频分析' },
            { value: 'snap', label: '事件抓拍分析' },
            { value: 'patrol', label: '周期巡检分析' },
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
            { value: 1, label: '已启用' },
            { value: 0, label: '已禁用' },
          ],
        },
      },
    ]
  }
}

