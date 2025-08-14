import {FormProps} from '@/components/Table';
import {BasicColumn} from '@/components/Table/src/types/table';

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '任务类型',
      dataIndex: 'taskType',
      width: 90,
      customRender: ({text}) => {
        if (text === 0) {
          return '实时帧捕获';
        } else if (text === 1) {
          return 'GB28181帧捕获';
        }
      },
    },
    {
      title: '任务编号',
      dataIndex: 'taskCode',
      width: 90,
    },
    {
      title: '任务名称',
      dataIndex: 'taskName',
      width: 120,
    },
    {
      title: 'RTMP流地址',
      dataIndex: 'rtmpUrl',
      width: 250,
    },
    {
      title: '设备ID',
      dataIndex: 'deviceId',
      width: 90,
    },
    {
      title: '通道ID',
      dataIndex: 'channelId',
      width: 90,
    },
    {
      width: 90,
      title: '操作',
      dataIndex: 'action',
    },
  ];
}

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: {span: 6},
    schemas: [
      {
        field: `taskType`,
        label: `任务类型`,
        component: 'Select',
        componentProps: {
          options: [
            {value: '', label: '全部'},
            {value: 0, label: '实时帧捕获'},
            {value: 1, label: 'GB28181帧捕获'},
          ],
        },
        defaultValue: '',
      },
      {
        field: `taskName`,
        label: `任务名称`,
        component: 'Input',
      },
    ],
  };
}
