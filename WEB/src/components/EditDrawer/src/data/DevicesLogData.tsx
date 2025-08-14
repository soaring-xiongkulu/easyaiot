import {FormProps} from '@/components/Table';
import {BasicColumn} from '@/components/Table/src/types/table';
import {Tag} from "ant-design-vue";

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '设备标识',
      dataIndex: 'deviceIdentification',
    },
    {
      title: '应用编码',
      dataIndex: 'appCode',
    },
    {
      title: '功能编码',
      dataIndex: 'functionCode',
    },
    {
      title: '功能名称',
      dataIndex: 'functionName',
    },
    {
      title: '状态',
      dataIndex: 'status',
      customRender: ({ text }) => {
        if (text === 0) {
          return <Tag color="green">成功</Tag>;
        } else if (text === 1) {
          return <Tag color="blue">未开始</Tag>;
        } else if (text === 2) {
          return <Tag color="yellow">上传中</Tag>;
        } else if (text === 3) {
          return <Tag color="red">失败</Tag>;
        }
      },
    },
    {
      title: '上传时间',
      dataIndex: 'uploadTime',
    },
    {
      title: '文件名称',
      dataIndex: 'fileName',
    },
    {
      title: '文件大小(单位KB)',
      dataIndex: 'fileSize',
    },
    {
      title: '创建时间',
      dataIndex: 'createdTime',
    },
    {
      width: 150,
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
        field: `appCode`,
        label: `应用编码`,
        component: 'Input',
      },
      {
        field: `functionCode`,
        label: `功能编码`,
        component: 'Input',
      },
      {
        field: `status`,
        label: `状态`,
        component: 'Select',
        componentProps: {
          options: [
            {value: '', label: '全部'},
            {value: 0, label: '成功'},
            {value: 1, label: '未开始'},
            {value: 2, label: '上传中'},
            {value: 2, label: '失败'},
          ],
        },
        defaultValue: '',
      },
    ],
  };
}
