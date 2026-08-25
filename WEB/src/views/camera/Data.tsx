import { BasicColumn, FormProps } from '@/components/Table';
import { Tag } from 'ant-design-vue';
import { formatLocationSummary, hasDeviceLocation } from './utils/deviceLocation';
import { isNvrListRow } from './utils/deviceLabel';
import { isGb28181SipListRow } from './utils/gb28181DeviceGroup';

function renderDeviceType(record: Record<string, unknown>) {
  if (isGb28181SipListRow(record as { device_kind?: string; id?: string })) {
    return <Tag color="purple">国标设备</Tag>;
  }
  if (isNvrListRow(record as { device_kind?: string; id?: string })) {
    return <Tag color="blue">NVR</Tag>;
  }
  return <Tag color="default">直连摄像头</Tag>;
}

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '设备名称',
      dataIndex: 'name',
      width: 180,
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'device_kind',
      width: 108,
      customRender: ({ record }) => renderDeviceType(record),
    },
    {
      title: '在线状态',
      dataIndex: 'online',
      width: 88,
      customRender: ({ text }) => (
        <Tag color={text ? 'green' : 'red'}>{text ? '在线' : '离线'}</Tag>
      ),
    },
    {
      title: 'IP地址',
      dataIndex: 'ip',
      width: 140,
      ellipsis: true,
      customRender: ({ text, record }) => {
        if (isNvrListRow(record) && record.port) {
          return `${text || '—'}:${record.port}`;
        }
        return text || '—';
      },
    },
    {
      title: '设备型号',
      dataIndex: 'model',
      width: 120,
      ellipsis: true,
      customRender: ({ text }) => text || '—',
    },
    {
      title: '制造商',
      dataIndex: 'manufacturer',
      width: 100,
      ellipsis: true,
      customRender: ({ text }) => text || '—',
    },
    {
      title: '所属NVR',
      dataIndex: 'nvr_label',
      width: 120,
      ellipsis: true,
      customRender: ({ text }) => text || '—',
    },
    {
      title: '接入节点',
      dataIndex: 'ingress_node_name',
      width: 170,
      ellipsis: true,
      customRender: ({ text, record }) => {
        const online = !record.ingress_node_id || record.ingress_node_status === 'online';
        const label = text || (record.ingress_node_id ? `边缘节点 #${record.ingress_node_id}` : '本机（主节点）');
        return <Tag color={online ? 'green' : 'red'}>{label}</Tag>;
      },
    },
    {
      title: '通道数',
      dataIndex: 'channel_count',
      width: 72,
      align: 'center',
      customRender: ({ text, record }) => {
        if (isGb28181SipListRow(record) || isNvrListRow(record)) {
          return text ?? record.channel_count ?? '—';
        }
        return '—';
      },
    },
    {
      title: '地图坐标',
      dataIndex: 'has_location',
      width: 168,
      ellipsis: true,
      customRender: ({ record }) => {
        if (hasDeviceLocation(record)) {
          return formatLocationSummary(record);
        }
        return <span style={{ color: 'rgba(0,0,0,0.25)' }}>未设置</span>;
      },
    },
    {
      title: '转发状态',
      dataIndex: 'stream_status',
      width: 96,
      align: 'center',
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 300,
      fixed: 'right',
      align: 'center',
    },
  ];
}

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: { span: 6 },
    showAdvancedButton: false,
    // 8 + 6 + 10 = 24，筛选项与查询/重置同一行且按钮靠右
    actionColOptions: {
      span: 10,
      style: { textAlign: 'right' },
    },
    schemas: [
      {
        field: 'deviceName',
        label: '设备名称',
        component: 'Input',
        colProps: { span: 8 },
        componentProps: {
          placeholder: '名称 / IP 模糊搜索',
        },
      },
      {
        field: 'online',
        label: '在线状态',
        component: 'Select',
        colProps: { span: 6 },
        componentProps: {
          options: [
            { value: '', label: '全部' },
            { value: true, label: '在线' },
            { value: false, label: '离线' },
          ],
        },
      },
    ],
  };
}
