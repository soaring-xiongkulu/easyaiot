import {BasicColumn, FormProps} from "@/components/Table";
import moment from "moment";
import {Tag} from "ant-design-vue";

//包类型
export const TYPE_OPTIONS = [
  {value: '', label: '全部'},
  {value: '0', label: '软件包'},
  {value: '1', label: '固件包'},
  {value: '2', label: 'APP包'},
  {value: '3', label: 'PC包'},
];

export const TYPE_MAP = {
  0: {label: '软件包', color: 'blue'},
  1: {label: '固件包', color: 'orange'},
  2: {label: 'APP包', color: 'green'},
  3: {label: 'PC包', color: 'purple'},
};

//状态[0:未验证,1:测试中,2:已发布,4:已撤回]
export const STATUS_MAP = {
  0: {label: '未验证', color: 'default'},
  1: {label: '测试中', color: 'processing'},
  2: {label: '已发布', color: 'success'},
  3: {label: '待发布', color: 'warning'},
  4: {label: '已撤回', color: 'error'},
};

export const STATUS_OPTIONS = [
  {value: '', label: '全部'},
  {value: '0', label: '未验证'},
  {value: '1', label: '测试中'},
  {value: '2', label: '已发布'},
  {value: '4', label: '已撤回'},
];

//发布策略[0:全量,1:灰度]
export const PUBLISH_STRATEGY_MAP = {
  0: {label: '全量', color: 'green'},
  1: {label: '灰度', color: 'gold'},
};

//灰度阶梯[1:设备级,2:产品级,3:全量]
export const GRAY_LADDER_MAP = {
  1: '设备级',
  2: '产品级',
  3: '全量',
};

//升级阶段[0:检测,1:命中,2:下载完成,3:下载失败,4:MD5校验失败,5:安装结果,6:启动成功]
export const PHASE_MAP = {
  0: {label: '检测', color: 'default'},
  1: {label: '命中', color: 'blue'},
  2: {label: '下载完成', color: 'cyan'},
  3: {label: '下载失败', color: 'red'},
  4: {label: 'MD5校验失败', color: 'volcano'},
  5: {label: '安装结果', color: 'geekblue'},
  6: {label: '启动成功', color: 'success'},
};

//升级记录筛选项
export const RECORD_TYPE_OPTIONS = [
  {value: '', label: '全部'},
  {value: '0', label: '软件包'},
  {value: '1', label: '固件包'},
  {value: '2', label: 'APP包'},
  {value: '3', label: 'PC包'},
];

export const RECORD_PHASE_OPTIONS = [
  {value: '', label: '全部'},
  {value: '0', label: '检测'},
  {value: '1', label: '命中'},
  {value: '2', label: '下载完成'},
  {value: '3', label: '下载失败'},
  {value: '4', label: 'MD5校验失败'},
  {value: '5', label: '安装结果'},
  {value: '6', label: '启动成功'},
];

export const RECORD_SUCCESS_OPTIONS = [
  {value: '', label: '全部'},
  {value: '1', label: '成功'},
  {value: '0', label: '失败'},
];

export function renderTypeTag(type) {
  const meta = TYPE_MAP[type] || TYPE_MAP[Number(type)];
  if (!meta) {
    return <span>-</span>;
  }
  return <Tag color={meta.color}>{meta.label}</Tag>;
}

export function renderStatusTag(status) {
  const meta = STATUS_MAP[status] || STATUS_MAP[Number(status)];
  if (!meta) {
    return <span>-</span>;
  }
  return <Tag color={meta.color}>{meta.label}</Tag>;
}

export function renderPhaseTag(phase) {
  const meta = PHASE_MAP[phase] || PHASE_MAP[Number(phase)];
  if (!meta) {
    return <span>-</span>;
  }
  return <Tag color={meta.color}>{meta.label}</Tag>;
}

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
      width: 60,
      customRender: ({text}) => renderTypeTag(text),
    },
    {
      title: '包版本号',
      dataIndex: 'version',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 60,
      customRender: ({record}) => {
        if (record.status === undefined || record.status === null) {
          return <span>-</span>;
        }
        return renderStatusTag(record.status);
      },
    },
    {
      title: '升级方式',
      dataIndex: 'upgradeMode',
      width: 50,
      customRender: ({text}) => {
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
      customRender: ({text}) => {
        if (text === 0) {
          return <Tag color="blue">否</Tag>;
        } else if (text === 1) {
          return <Tag color="orange">是</Tag>;
        }
      },
    },
    {
      title: '测试',
      dataIndex: 'testPassed',
      width: 50,
      customRender: ({text}) => {
        if (text === 1) {
          return <Tag color="success">通过</Tag>;
        } else if (text === 0 && text !== null && text !== undefined) {
          return <Tag color="error">未通过</Tag>;
        }
        return <span>-</span>;
      },
    },
    {
      title: '发布策略',
      dataIndex: 'publishStrategy',
      width: 70,
      customRender: ({record}) => {
        const strategyMeta = PUBLISH_STRATEGY_MAP[record.publishStrategy];
        if (!strategyMeta) {
          return <span>-</span>;
        }
        let text = strategyMeta.label;
        if (record.publishStrategy === 1 && record.grayLadder && GRAY_LADDER_MAP[record.grayLadder]) {
          text += '-' + GRAY_LADDER_MAP[record.grayLadder];
        }
        return <Tag color={strategyMeta.color}>{text}</Tag>;
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
          options: TYPE_OPTIONS,
        },
        defaultValue: '',
      },
      {
        field: `version`,
        label: `包版本号`,
        component: 'Input',
      },
      {
        field: `status`,
        label: `状态`,
        component: 'Select',
        componentProps: {
          options: STATUS_OPTIONS,
        },
        defaultValue: '',
      },
    ],
  };
}
