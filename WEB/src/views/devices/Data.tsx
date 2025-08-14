import {FormProps} from '@/components/Table';
import {BasicColumn} from '@/components/Table/src/types/table';
import moment from 'moment/moment';
import {Tag} from "ant-design-vue";
import {getDeviceProfiles} from "@/api/device/product";

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '应用场景',
      dataIndex: 'appId',
      width: 90,
    },
    {
      title: '设备名称',
      dataIndex: 'deviceName',
      width: 120,
    },
    {
      title: '设备标识',
      dataIndex: 'deviceIdentification',
      width: 120,
    },
    {
      title: '设备SN号',
      dataIndex: 'deviceSn',
      width: 120,
    },
    {
      width: 90,
      title: '产品类型',
      dataIndex: 'deviceType',
      customRender: ({text}) => {
        return <Tag
          color={text == 'COMMON' ? 'blue' : text == 'GATEWAY' ? 'purple' : 'cyan'}>{text == 'COMMON' ? '普通产品' : text == 'GATEWAY' ? '网关产品' : text == 'VIDEO_COMMON' ? '视频产品' : '子设备'}</Tag>;
      },
    },
    {
      title: '所属产品',
      dataIndex: 'productName',
      width: 120,
    },
    {
      title: '连接状态',
      dataIndex: 'connectStatus',
      width: 90,
    },
    {
      title: '激活状态',
      dataIndex: 'activeStatus',
      width: 60,
    },
    {
      title: '设备版本',
      dataIndex: 'deviceVersion',
      width: 80,
    },
    {
      title: '激活时间',
      dataIndex: 'activatedTime',
      width: 150,
      customRender: ({record}) => {
        if (record.activatedTime === null) {
          return '';
        } else {
          return <div>{moment(record.activatedTime).format('YYYY-MM-DD HH:mm:ss')} </div>;
        }
      },
    },
    {
      title: '最后上线时间',
      width: 150,
      dataIndex: 'lastOnlineTime',
      customRender: ({record}) => {
        if (record.lastOnlineTime === null) {
          return '';
        } else {
          return <div>{moment(record.lastOnlineTime).format('YYYY-MM-DD HH:mm:ss')} </div>;
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
        field: `deviceName`,
        label: `设备名称`,
        component: 'Input',
      },
      {
        field: `productIdentification`,
        label: `所属产品`,
        component: 'ApiSelect',
        componentProps: {
          api: getDeviceProfiles,
          beforeFetch: () => {
            return {
              page: 1,
              pageSize: 100,
            };
          },
          resultField: 'data',
          // use name as label
          labelField: 'productName',
          // use id as value
          valueField: 'productIdentification',
        },
      },
      {
        field: `deviceIdentification`,
        label: `设备标识`,
        component: 'Input',
      },
      {
        field: `deviceSn`,
        label: `设备SN号`,
        component: 'Input',
      },
      {
        field: `connectStatus`,
        label: `连接状态`,
        component: 'Select',
        componentProps: {
          options: [
            {value: '', label: '全部'},
            {value: 'ONLINE', label: '在线'},
            {value: 'OFFLINE', label: '离线'},
          ],
        },
        defaultValue: '',
      },
      {
        field: `deviceType`,
        label: `产品类型`,
        component: 'Select',
        componentProps: {
          options: [
            {value: '', label: '全部'},
            {value: 'COMMON', label: '普通产品'},
            {value: 'GATEWAY', label: '网关产品'},
            {value: 'SUBSET', label: '子设备'},
          ],
        },
        defaultValue: '',
      },
      {
        field: `activeStatus`,
        label: `激活状态`,
        component: 'Select',
        componentProps: {
          options: [
            {value: '', label: '全部'},
            {value: 1, label: '已激活'},
            {value: 0, label: '未激活'},
          ],
        },
        defaultValue: '',
      },
    ],
  };
}
