import Icon from '@/components/Icon/index';
import type { Rule } from 'ant-design-vue/es/form';
import corpMessage from '@/assets/images/corp-message.png';
import feishuLogo from '@/assets/images/notice/feishu.png';

// 表单
export const formSchemas = ({ isVariable }) => {
  return [
    {
      field: 'id',
      component: 'Input',
      colProps: {
        span: 0,
      },
    },
    {
      field: 'msgName',
      component: 'Input',
      required: true,
      label: '消息名称',
    },
    {
      field: 'userGroupId',
      component: 'Input',
      required: true,
      label: '用户分组',
      slot: 'userGroupId',
      ifShow: ({ values }) => {
        return values?.msgType != '5';
      },
    },
    {
      field: 'variableDefinitions',
      label: '变量列表',
      component: 'Input',
      slot: 'variableDefinitions',
      colProps: {
        span: 24,
      },
      show: () => {
        return isVariable?.value;
      },
    },
  ];
};

function renderProvider(type: string, icon: string, text: string) {
  return (
    <div class={'message-item active'}>
      {type == 'icon' ? <Icon icon={icon} size={'67'} /> : <img src={icon} />}
      <span>{text}</span>
    </div>
  );
}

function _renderProvider({ config, getFieldsValue, setFieldsValue }) {
  const { msgType } = getFieldsValue && getFieldsValue();
  const handleChange = (value) => {
    setFieldsValue && setFieldsValue({ msgType: value });
  };
  return (
    <div class={'message-warpper'}>
      {config.map((item) => {
        const { type, icon, text, value } = item;
        const className = msgType == value ? 'message-item active' : 'message-item';
        return (
          <div class={className} onClick={handleChange.bind(null, value)}>
            {type == 'icon' ? <Icon icon={icon} size={'67'} /> : <img src={icon} />}
            <span>{text}</span>
          </div>
        );
      })}
    </div>
  );
}

export const msgTypeFiled = [
  {
    field: 'msgType',
    component: 'Input',
    colProps: {
      span: 0,
    },
  },
];

export const emailSchemas = () => {
  return [
    ...msgTypeFiled,
    {
      field: 'title',
      component: 'Input',
      required: true,
      label: '邮件标题',
    },
    {
      field: 'cc',
      component: 'Select',
      label: '抄送',
      componentProps: {
        mode: 'tags',
      },
      rules: [
        {
          validator(_rule: Rule, value: string[]) {
            const regEmail = /^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/;
            let error;
            if (value) {
              value.some((item: string) => {
                if (!regEmail.test(item)) {
                  error = item;
                  return true;
                }
                return false;
              });
            }
            if (error) return Promise.reject(error ? `${error}邮件格式错误` : '');
            else return Promise.resolve();
          },
        },
      ],
    },
    {
      field: 'files',
      component: 'Input',
      label: '附件信息',
      slot: 'attachments',
    },
    {
      field: 'content',
      label: '邮件正文',
      required: true,
      component: 'Input',
      slot: 'message',
      colProps: {
        span: 24,
      },
    },
  ];
};

export const smsSchemas = ({ getFieldsValue, setFieldsValue }) => {
  return [
    {
      field: 'msgType',
      component: 'Input',
      required: true,
      label: '类型',
      render() {
        const config = [
          {
            type: 'icon',
            icon: 'ph:chat-circle-dots-light',
            text: '阿里云短信',
            value: 1,
          },
          {
            type: 'icon',
            icon: 'ph:chat-circle-dots-light',
            text: '腾讯云短信',
            value: 2,
          },
        ];
        return _renderProvider({ config, getFieldsValue, setFieldsValue });
      },
    },
    {
      field: 'templateId',
      required: true,
      component: 'Input',
      label: '短信模版ID',
      // slot: 'smsTemplate',
    },
    {
      field: 'templateDataList',
      label: '短信模版',
      slot: 'templateDataList',
      component: 'Input',
    },
  ];
};

const commonConfigFileds = [
  {
    field: 'title',
    component: 'Input',
    label: '标题',
    ifShow: ({ values }) => {
      return (
        ['图文消息', '文本卡片消息'].includes(values.cpMsgType) ||
        ['链接消息', 'markdown消息'].includes(values.dingMsgType) ||
        values.dingMsgType == '卡片消息'
      );
    },
  },

  {
    field: 'url',
    component: 'Input',
    label: '跳转URL',
    ifShow: ({ values }) => {
      return (
        ['图文消息', '文本卡片消息'].includes(values.cpMsgType) || values.dingMsgType == '链接消息'
      );
    },
  },
  {
    field: 'btnUrl;',
    component: 'Input',
    label: '跳转URL',
    ifShow: ({ values }) => {
      return values.dingMsgType == '卡片消息';
    },
  },
  {
    field: 'imgUrl',
    component: 'Input',
    label: '图片URL',
    ifShow: ({ values }) => {
      return values.cpMsgType == '图文消息' || values.dingMsgType == '链接消息';
    },
  },
  {
    field: 'btnText',
    component: 'Input',
    label: '按钮文字',
    ifShow: ({ values }) => {
      return values.cpMsgType == '文本卡片消息' || values.dingMsgType == '卡片消息';
    },
  },
  {
    field: 'content',
    label: '消息内容',
    // required: true,
    component: 'Input',
    slot: 'message',
    colProps: {
      span: 24,
    },
    ifShow: ({ values }) => {
      return (
        [values.cpMsgType, values.dingMsgType].includes('文本消息') ||
        ['链接消息', '卡片消息'].includes(values.dingMsgType) ||
        [(values.cpMsgType, values.dingMsgType)].includes('markdown消息')
      );
    },
  },
  {
    field: 'describe',
    component: 'InputTextArea',
    label: '描述',
    ifShow: ({ values }) => {
      return values.cpMsgType == '图文消息' || values.cpMsgType == '文本卡片消息';
    },
  },
];

export const weixinSchemas = () => {
  return [
    {
      field: 'msgType',
      component: 'Input',
      label: '类型',
      render() {
        return renderProvider('img', corpMessage, '企业消息');
      },
    },
    {
      field: 'agentId',
      component: 'Select',
      label: '应用',
      slot: 'agentId',
      required: true,
    },
    {
      field: 'cpMsgType',
      component: 'Select',
      label: '消息类型',
      componentProps: {
        options: [
          { value: '图文消息', label: '图文消息' },
          { value: '文本消息', label: '文本消息' },
          { value: '文本卡片消息', label: '文本卡片消息' },
          { value: 'markdown消息', label: 'markdown消息' },
        ],
      },
    },
    ...commonConfigFileds,
  ];
};

export const dindinSchemas = () => {
  return [
    ...msgTypeFiled,
    {
      field: 'radioType',
      component: 'RadioGroup',
      label: '消息通知方式',
      componentProps: {
        options: [
          { label: '工作通知方式', value: '工作通知方式' },
          { label: '群机器人消息', value: '群机器人消息' },
        ],
      },
    },
    {
      field: 'agentId',
      component: 'Select',
      label: '应用',
      required: true,
      slot: 'agentId',
      ifShow: ({ values }) => {
        return values.radioType == '工作通知方式';
      },
    },
    {
      field: 'webHook',
      component: 'Input',
      label: 'webHook',
      ifShow: ({ values }) => {
        return values.radioType == '群机器人消息';
      },
    },
    {
      field: 'dingMsgType',
      component: 'Select',
      label: '消息类型',
      componentProps: {
        options: [
          { value: '链接消息', label: '链接消息' },
          { value: '文本消息', label: '文本消息' },
          { value: '卡片消息', label: '卡片消息' },
          { value: 'markdown消息', label: 'markdown消息' },
        ],
      },
    },
    ...commonConfigFileds,
  ];
};

export const feishuSchemas = () => {
  return [
    {
      field: 'msgType',
      component: 'Input',
      label: '类型',
      render() {
        return renderProvider('img', feishuLogo, '飞书');
      },
    },
    ...msgTypeFiled,
    {
      field: 'radioType',
      component: 'RadioGroup',
      label: '消息通知方式',
      componentProps: {
        options: [
          { label: '群机器人消息', value: '群机器人消息' },
        ],
      },
      defaultValue: '群机器人消息',
    },
    {
      field: 'webHook',
      component: 'Input',
      label: 'Webhook地址',
      required: true,
      ifShow: ({ values }) => {
        return values.radioType == '群机器人消息';
      },
    },
    {
      field: 'feishuMsgType',
      component: 'Select',
      label: '消息类型',
      componentProps: {
        options: [
          { value: '文本消息', label: '文本消息' },
          { value: '富文本消息', label: '富文本消息' },
          { value: '卡片消息', label: '卡片消息' },
        ],
      },
      defaultValue: '文本消息',
    },
    ...commonConfigFileds,
  ];
};

export const httpSchemas = () => {
  return [
    ...msgTypeFiled,
    {
      field: 'method',
      component: 'Select',
      label: 'URL',
      required: true,
      componentProps: {
        options: [
          { label: 'GET', value: 'GET' },
          { label: 'POST', value: 'POST' },
          { label: 'PUT', value: 'PUT' },
          { label: 'PATCH', value: 'PATCH' },
          { label: 'DELETE', value: 'DELETE' },
          { label: 'HEAD', value: 'HEAD' },
          { label: 'OPTIONS', value: 'OPTIONS' },
        ],
        // onChange: () => {
        //   setFieldsValue({
        //     body: ' ',
        //     bodyType: 'text/plain',
        //   });
        // },
      },
      colProps: {
        span: 5,
      },
    },
    {
      field: 'url',
      component: 'Input',
      label: ' ',
      itemProps: {
        class: 'hidden-label',
      },
      colProps: {
        span: 19,
      },
      rules: [{ required: true, message: '请输入URL' }],
    },
    {
      field: 'tabActive',
      component: 'Input',
      label: ' ',
      slot: 'tabActive',
      itemProps: {
        class: 'none-label',
      },
    },
    {
      field: 'bodyType',
      component: 'Select',
      label: ' ',
      required: true,
      componentProps: {
        options: [
          { label: 'text/plain', value: 'text/plain' },
          { label: 'application/json', value: 'application/json' },
          { label: 'application/javascript', value: 'application/javascript' },
          { label: 'application/xml', value: 'application/xml' },
          { label: 'text/xml', value: 'text/xml' },
          { label: 'text/html', value: 'text/html' },
        ],
      },
      colProps: {
        span: 24,
      },
      itemProps: {
        class: 'none-label',
      },
      defaultValue: 'text/plain',
      ifShow: ({ values }) => {
        return values?.tabActive == 'Body';
      },
    },
    {
      field: 'body',
      label: '消息内容',
      component: 'Input',
      slot: 'message',
      ifShow: ({ values }) => {
        return values?.tabActive == 'Body';
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
      const config = {
        1: '阿里云短信',
        2: '腾讯云短信',
        3: 'EMail',
        4: '企业微信',
        5: 'Webhook',
        6: '钉钉',
        7: '飞书',
      };
      return config[value] ?? '--';
    },
  },
  {
    field: 'msgName',
    label: '消息名称',
  },
  {
    field: 'userGroupName',
    label: '用户组',
    show: (data) => {
      return data?.msgType != 5;
    },
  },
];

export const emailDetailSchemas = [
  ...commonDetailSchema,
  {
    field: 'title',
    label: '标题',
    span: 3,
  },
  {
    field: 'cc',
    label: '抄送',
    span: 3,
  },
  {
    field: 'files',
    label: '附件',
    span: 3,
    render: (data) => {
      return data ? JSON.parse(data || '{}')?.filePath : '--';
    },
  },
  {
    field: 'content',
    label: '内容',
    span: 3,
  },
];

export const smsDetailSchemas = [
  ...commonDetailSchema,
  {
    field: 'templateId',
    label: '模版ID',
    span: 3,
  },
];

export const weixinDetailSchemas = [
  ...commonDetailSchema,
  {
    field: 'cpMsgType',
    label: '消息类型',
  },
  {
    field: 'agentId',
    label: '应用',
  },
  {
    field: 'title',
    label: '标题',
  },
  {
    field: 'imgUrl',
    label: '图片URL',
  },
  {
    field: 'url',
    label: '跳转URL',
  },
  {
    field: 'content',
    label: '内容',
  },
  {
    field: 'describe',
    label: '描述',
  },
];

export const dingDetailSchemas = [
  ...commonDetailSchema,
  {
    field: 'radioType',
    label: '通知方式',
  },
  {
    field: 'dingMsgType',
    label: '消息类型',
  },
  {
    field: 'agentId',
    label: '应用',
    show: (data) => {
      return data?.dingMsgType == '工作通知方式';
    },
  },
  {
    field: 'webHook',
    label: 'webHook',
    show: (data) => {
      return data?.dingMsgType == '群机器人消息';
    },
  },
  {
    field: 'title',
    label: '标题',
  },

  {
    field: 'picUrl',
    label: '图片URL',
  },
  {
    field: 'btnTxt',
    label: '按钮文案',
  },
  {
    field: 'btnUrl',
    label: '按钮UR',
  },
  {
    field: 'url',
    label: '跳转URL',
  },
  {
    field: 'content',
    label: '内容',
  },
];

export const httpDetailSchemas = [
  ...commonDetailSchema,
  {
    field: 'method',
    label: '方法',
  },
  {
    field: 'url',
    label: 'URL',
    span: 3,
  },
];

// 操作
export const templateColumns = [
  {
    title: 'Name',
    dataIndex: 'name',
  },
  {
    title: 'Value',
    dataIndex: 'value',
  },
  {
    title: '操作',
    dataIndex: 'operation',
    width: 80,
    fixed: 'right',
  },
];
