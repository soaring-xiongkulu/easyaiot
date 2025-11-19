import {BasicColumn, FormProps} from "@/components/Table";
import moment from "moment";
import {Tag} from "ant-design-vue";

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '包名称',
      dataIndex: 'name',
      width: 90,
    },
    {
      title: '包类型',
      dataIndex: 'type',
      width: 50,
      customRender: ({ text }) => {
        if (text === '0') {
          return <Tag color="blue">软件包</Tag>;
        } else if (text === '1') {
          return <Tag color="orange">固件包</Tag>;
        }
      },
    },
    {
      title: '包版本号',
      dataIndex: 'version',
      width: 90,
    },
    {
      title: '升级方式',
      dataIndex: 'upgradeMode',
      width: 50,
      customRender: ({ text }) => {
        if (text === 0) {
          return <Tag color="blue">非强制升级</Tag>;
        } else if (text === 1) {
          return <Tag color="orange">强制升级</Tag>;
        }
      },
    },
    {
      title: '关键版本',
      dataIndex: 'keyVersionFlag',
      width: 50,
      customRender: ({ text }) => {
        if (text === 0) {
          return <Tag color="blue">否</Tag>;
        } else if (text === 1) {
          return <Tag color="orange">是</Tag>;
        }
      },
    },
    {
      title: '上传时间',
      width: 90,
      dataIndex: 'uploadTime',
      customRender: ({record}) => {
        if (record.uploadTime === null) {
          return '';
        } else {
          return <div>{moment(record.uploadTime).format('YYYY-MM-DD HH:mm:ss')} </div>;
        }
      },
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
      width: 80,
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
        field: `name`,
        label: `包名称`,
        component: 'Input',
      },
      {
        field: `type`,
        label: `包类型`,
        component: 'Select',
        componentProps: {
          options: [
            {value: '', label: '全部'},
            {value: '0', label: '软件包'},
            {value: '1', label: '固件包'},
            {value: '2', label: '电控包'},
          ],
        },
        defaultValue: '',
      },
      {
        field: `version`,
        label: `包版本号`,
        component: 'Input',
      },
    ],
  };
}
