import {BasicColumn, FormProps} from "@/components/Table";
import moment from "moment";
import {Tag} from "ant-design-vue";

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '设备名称',
      dataIndex: 'name',
      width: 90,
    },
    {
      title: '设备编号',
      dataIndex: 'deviceIdentification',
      width: 90,
    },
    {
      title: '地址',
      dataIndex: 'localIp',
      width: 90,
    },
    {
      title: '端口',
      dataIndex: 'port',
      width: 90,
    },
    {
      title: '信令传输协议',
      dataIndex: 'transport',
      width: 90,
    },
    {
      title: '流传输模式',
      dataIndex: 'streamMode',
      width: 90,
    },
    {
      title: '是否在线',
      dataIndex: 'onLine',
      width: 90,
      customRender: ({text}) => {
        return (
          <Tag color={text ? 'green' : 'red'}>
            {text ? '在线' : '离线'}
          </Tag>
        );
      },
    },
    {
      title: '注册时间',
      dataIndex: 'registerTime',
      width: 90,
    },
    {
      title: '通道个数',
      dataIndex: 'channelCount',
      width: 90,
    },
    {
      title: '更新时间',
      width: 90,
      dataIndex: 'updatedTime',
      customRender: ({record}) => {
        if (record.updatedTime === null) {
          return '';
        } else {
          return <div>{moment(record.updatedTime).format('YYYY-MM-DD HH:mm:ss')} </div>;
        }
      },
    },
    {
      width: 110,
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
        field: `deviceIdentification`,
        label: `设备国标编号`,
        component: 'Input',
      },
      {
        field: `name`,
        label: `设备名称`,
        component: 'Input',
      },
    ],
  };
}
