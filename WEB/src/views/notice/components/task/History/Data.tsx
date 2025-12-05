import type { FormProps } from '/@/components/Form';
import { BasicColumn } from '/@/components/Table/src/types/table';
import { formatToDateTime } from '/@/utils/dateUtil';
import { Tooltip } from 'ant-design-vue';

const msgTypeOptions = {
  1: '阿里云短信',
  2: '腾讯云短信',
  3: 'EMail',
  4: '企业微信',
  5: 'Webhook',
  6: '钉钉',
  7: '飞书',
};

export const getColumns = (): BasicColumn[] => {
  return [
    {
      title: '消息名称',
      dataIndex: 'msgName',
      width: 220,
    },
    {
      title: '创建时间',
      dataIndex: 'createTime',
      format(val) {
        return val ? formatToDateTime(val) : '-';
      },
      width: 270,
    },
    {
      title: '推送结果',
      dataIndex: 'result',
      ellipsis: true,
      customRender({ value }) {
        return <Tooltip title={value}>{value}</Tooltip>;
      },
    },
  ];
};

export const getFormConfig = (): FormProps => {
  return {
    labelWidth: 70,
    baseColProps: { span: 6 },
    schemas: [
      {
        field: `msgName`,
        label: `消息名称`,
        component: 'Input',
      }
    ],
  };
};
