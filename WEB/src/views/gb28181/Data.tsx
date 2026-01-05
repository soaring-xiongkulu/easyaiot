import {Badge} from "ant-design-vue";
import {Icon} from "@/components/Icon";

export const getTableColumns = () => {
  return [
    {
      title: '类型',
      dataIndex: 'msgType',
      customRender: ({text}) => {
        return {
          1: '阿里云短信',
          2: '腾讯云短信',
          3: 'EMail',
          4: '企业微信',
          5: 'http',
          6: '钉钉',
        }[text];
      },
    },
    {
      width: 140,
      title: '操作',
      dataIndex: 'action',
    },
  ];
};

export const getFormConfig = () => {
  return {
    labelWidth: 70,
    baseColProps: {span: 6},
    schemas: [
      {
        field: `msgType`,
        label: `消息类型`,
        component: 'Select',
        componentProps: {
          options: [
            { label: '阿里云短信', value: '1' },
            { label: '腾讯云短信', value: '2' },
            { label: 'EMail', value: '3' },
            { label: '企业微信', value: '4' },
            { label: 'http', value: '5' },
            { label: '钉钉', value: '6' },
          ],
        },
      },
    ],
  };
};

export const formSchemas = (handleNoticeType) => {
  return [
    {
      field: 'id',
      component: 'Input',
      colProps: {
        span: 0,
      },
    },
    {
      field: 'msgType',
      component: 'Select',
      label: '消息类型',
      required: true,
      componentProps: {
        options: [
          {label: '阿里云短信', value: 1},
          {label: '腾讯云短信', value: 2},
          {label: '邮件', value: 3},
          {label: '企业号/企业微信', value: 4},
          {label: 'HTTP请求', value: 5},
          {label: '钉钉', value: 6},
        ],
        onChange: (e) => {
          handleNoticeType(e);
        },
      },
      defaultValue: 3,
    },
  ];
};

export const emailSchemas = () => {
  return [
    {
      field: 'mailHost',
      component: 'Input',
      label: '邮件服务器的SMTP地址',
      required: true,
      colProps: {
        span: 11,
      },
    },
    {
      field: 'mailPort',
      component: 'InputNumber',
      label: '邮件服务器的SMTP端口',
      colProps: {
        span: 11,
        push: 2,
      },
      rules: [{required: true, message: '请输入端口号'}],
    },

    {
      field: 'mailFrom',
      component: 'Input',
      required: true,
      label: '发件人（邮箱地址）',
    },
    {
      field: 'mailUser',
      component: 'Input',
      required: true,
      label: '用户名',
    },
    {
      field: 'mailPassword',
      required: true,
      component: 'InputPassword',
      label: '密码',
    },
    {
      field: 'starttlsEnable',
      component: 'Checkbox',
      label: '使用STARTTLS安全连接',
      colProps: {
        span: 11,
      },
      itemProps: {
        class: 'checkbox-warpper',
      },
    },
    {
      field: 'sslEnable',
      component: 'Checkbox',
      label: '使用SSL安全连接',
      colProps: {
        span: 11,
        push: 2,
      },
      itemProps: {
        class: 'checkbox-warpper',
      },
      labelWidth: '130px',
    },
  ];
};

export const aliyunSchemas = () => {
  return [
    {
      field: 'aliyunAccessKeyId',
      required: true,
      component: 'Input',
      label: 'AccessKeyId',
    },
    {
      field: 'aliyunAccessKeySecret',
      required: true,
      component: 'InputPassword',
      label: 'AccessKeySecret',
    },
    {
      field: 'aliyunSign',
      required: true,
      component: 'Input',
      label: '短信签名',
    },
  ];
};

export const tenxunyunSchemas = () => {
  return [
    {
      field: 'txyunAppId',
      required: true,
      component: 'Input',
      label: 'AccessKeyId',
    },
    {
      field: 'txyunAppKey',
      required: true,
      component: 'InputPassword',
      label: 'AccessKeySecret',
    },
    {
      field: 'txyunSign',
      required: true,
      component: 'Input',
      label: '短信签名',
    },
  ];
};

export const weixinSchemas = () => {
  return [
    {
      field: 'wxCpCorpId',
      required: true,
      component: 'Input',
      label: '企业ID',
    },
    {
      field: 'weixinApply',
      component: 'Input',
      label: '应用',
      slot: 'weixinApply',
    },
  ];
};

export const dindinSchemas = () => {
  return [
    {
      field: 'dindinApply',
      component: 'Input',
      label: '应用',
      slot: 'dindinApply',
    },
  ];
};

export const httpSchemas = () => {
  return [
    {
      field: 'isHttpUseProxy',
      component: 'Checkbox',
      label: '使用HTTP代理',
      defaultValue: true,
      itemProps: {
        class: 'checkbox-warpper',
      },
      labelWidth: '110px',
    },
    {
      field: 'host',
      component: 'Input',
      label: 'Host',
      required: true,
      colProps: {
        span: 11,
      },
      componentProps: {},
      ifShow: ({values}) => {
        return values?.isHttpUseProxy;
      },
    },
    {
      field: 'port',
      component: 'Input',
      label: '端口',
      required: true,
      colProps: {
        span: 11,
        push: 2,
      },
      ifShow: ({values}) => {
        return values?.isHttpUseProxy;
      },
    },
    {
      field: 'userName',
      component: 'Input',
      required: true,
      label: '用户名',
      ifShow: ({values}) => {
        return values?.isHttpUseProxy;
      },
    },
    {
      field: 'password',
      component: 'Input',
      required: true,
      label: '密码',
      ifShow: ({values}) => {
        return values?.isHttpUseProxy;
      },
    },
  ];
};

// 详情
export const commonDetailSchema = [
  {
    field: 'msgType',
    label: '消息类型',
    render: (value) => {
      return {
        1: '阿里云短信',
        2: '腾讯云短信',
        3: 'EMail',
        4: '企业微信',
        5: 'http',
        6: '钉钉',
      }[value];
    },
  },
];

export const emailDetailSchemas = [
  ...commonDetailSchema,
  {
    field: 'mailHost',
    label: '邮件服务器的SMTP地址',
  },
  {
    field: 'mailPort',
    label: '邮件服务器的SMTP端口',
  },
  {
    field: 'mailFrom',
    label: '发件人（邮箱地址）',
  },
  {
    field: 'mailUser',
    label: '用户名',
  },
  {
    field: 'mailPassword',
    label: '密码',
  },
  {
    field: 'starttlsEnable',
    label: '使用STARTTLS安全连接',
    render: (value) => {
      return value ? '是' : '否';
    },
  },
  {
    field: 'sslEnable',
    label: '使用SSL安全连接',
    render: (value) => {
      return value ? '是' : '否';
    },
  },
];

export const aliyunDetailSchemas = [
  ...commonDetailSchema,
  {
    field: 'aliyunAccessKeyId',
    label: 'AccessKeyId',
  },
  {
    field: 'aliyunAccessKeySecret',
    label: 'AccessKeySecret',
  },
  {
    field: 'aliyunSign',
    label: '短信签名',
  },
];

export const tengxunyunDetailSchemas = [
  ...commonDetailSchema,
  {
    field: 'txyunAppId',
    label: 'AccessKeyId',
  },
  {
    field: 'txyunAppKey',
    label: 'AccessKeyId',
  },
  {
    field: 'txyunSign',
    label: '短信签名',
  },
];
export const weixinDetailSchemas = [
  {
    field: 'wxCpCorpId',
    label: '企业ID',
  },
  ...commonDetailSchema,
];

export const dingDetailSchemas = [...commonDetailSchema];

export const httpDetailSchemas = [
  ...commonDetailSchema,
  {
    field: 'isHttpUseProxy',
    label: '使用HTTP代理',
    render: (value) => {
      return value ? '是' : '否';
    },
  },
  {
    field: 'host',
    label: 'HOST',
  },
  {
    field: 'port',
    label: '端口',
  },
  {
    field: 'userName',
    label: '用户名',
  },
  {
    field: 'password',
    label: '密码',
  },
];

// editTable

export const weixinApplyColumns = [
  {
    title: '应用名称',
    dataIndex: 'appName',
  },
  {
    title: 'AgentId',
    dataIndex: 'agentId',
  },
  {
    title: 'Secret',
    dataIndex: 'secret',
  },
  {
    title: '操作',
    dataIndex: 'operation',
    width: 80,
    fixed: 'right',
  },
];

export const dindinApplyColumns = [
  {
    title: '应用名称',
    dataIndex: 'appName',
  },
  {
    title: 'AgentId',
    dataIndex: 'agentId',
  },
  {
    title: 'AppKey',
    dataIndex: 'appKey',
  },
  {
    title: 'AppSecret',
    dataIndex: 'appSecret',
  },
  {
    title: '操作',
    dataIndex: 'operation',
    width: 80,
    fixed: 'right',
  },
];

// 通知记录
export const getRecordColumns = (handleViewDetail) => {
  return [
    {
      title: 'ID',
      dataIndex: 'id',
    },
    {
      title: '发送时间',
      dataIndex: 'notifyTime',
    },
    {
      title: '状态',
      dataIndex: 'state',
      customRender: ({text, record}) => {
        return (
          <div class={'state'}>
            <Badge color={text == 'error' ? 'red' : 'green'} text={text}/>
            <Icon
              icon={'ph:warning-circle-light'}
              color={'#0084f4'}
              onClick={() => {
                handleViewDetail && handleViewDetail(true, record);
              }}
            />
          </div>
        );
      },
    },
    {
      width: 80,
      title: '操作',
      dataIndex: 'action',
    },
  ];
};

export const getRecordFormConfig = () => {
  return {
    labelWidth: 30,
    baseColProps: {span: 6},
    schemas: [
      // {
      //   field: `notifyTime`,
      //   label: `发送时间`,
      //   component: 'DatePicker',
      // },
      {
        field: `id`,
        label: `ID`,
        component: 'Input',
      },

      // {
      //   field: `state`,
      //   label: `状态`,
      //   component: 'Select',
      //   componentProps: {
      //     options: [
      //       { label: '成功', value: 'succes' },
      //       { label: '失败', value: 'error' },
      //     ],
      //   },
      // },
    ],
  };
};
