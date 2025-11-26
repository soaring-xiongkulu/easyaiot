import {BasicColumn} from '@/components/Table/src/types/table';
import {FormProps} from '@/components/Table';

import {Tag, Tooltip} from 'ant-design-vue';
import {formatToDateTime} from "@/utils/dateUtil";

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '产品ID',
      dataIndex: 'id',
      defaultHidden: true
    },
    {
      title: '应用场景',
      dataIndex: 'appId',
      width: 70,
    },
    {
      title: '产品名称',
      dataIndex: 'productName',
      width: 70,
    },
    {
      title: '产品标识',
      dataIndex: 'productIdentification',
      width: 90,
    },
    {
      title: '产品类型',
      dataIndex: 'productType',
      width: 50,
      customRender: ({ text }) => {
        return <Tag color={text=='COMMON' ? 'blue' : text=='GATEWAY'? 'green' : 'yellow'}>{text=='COMMON' ? '普通产品' : text=='GATEWAY'? '网关产品' : '子设备'}</Tag>;
      },
    },
    {
      title: '产品型号',
      dataIndex: 'model',
      width: 50,
    },
    {
      title: '厂商ID',
      dataIndex: 'manufacturerId',
      width: 50,
    },
    {
      title: '厂商名称',
      dataIndex: 'manufacturerName',
      width: 50,
    },
    {
      title: '产品型号',
      dataIndex: 'model',
      width: 50,
    },
    {
      title: '数据格式',
      dataIndex: 'dataFormat',
      width: 50,
    },
    {
      title: '设备类型',
      dataIndex: 'deviceType',
      width: 50,
    },
    {
      title: '协议类型',
      dataIndex: 'protocolType',
      width: 50,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 50,
      customRender: ({ text }) => {
        return <Tag color={text ? 'green' : 'red'}>{text ? '启用' : '停用'}</Tag>;
      },
    },
    {
      title: '产品描述',
      dataIndex: 'remark',
      width: 50,
    },
    {
      title: '创建时间',
      dataIndex: 'createTime',
      width: 110,
      customRender({ value }) {
        return (
          <Tooltip title={formatToDateTime(value)}>
            <span class={'ellipsis-span'}>{formatToDateTime(value)}</span>
          </Tooltip>
        );
      },
      ellipsis: true,
    },
    {
      width: 110,
      title: '操作',
      dataIndex: 'action',
    },
    // {
    //   title: '配置图片',
    //   dataIndex: 'imageData',
    //   width: 60,
    //   customRender: ({ text }) => {
    //     return (
    //       <div
    //         class={'product-image'}
    //         onClick={() => {
    //           if (!text) return;
    //           createImgPreview({ imageList: [text] });
    //         }}
    //       >
    //         <img src={text ? text : defaultPic} />
    //       </div>
    //     );
    //   },
    // },
  ];
}

// function filterCategoryTree(list: Array): Array {
//   return list.map((item) => {
//     item.key = item.value = item.id;
//     item.title = item.name;
//     if (item.children && item.children.length > 0) {
//       filterCategoryTree(item.children);
//     }
//     return item;
//   });
// }

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 70,
    baseColProps: { span: 6 },
    schemas: [
      {
        field: `productName`,
        label: `产品名称`,
        component: 'Input',
      },
      {
        field: `model`,
        label: `产品型号`,
        component: 'Input',
      },
      {
        field: `manufacturerName`,
        label: `厂商名称`,
        component: 'Input',
      },
    ],
  };
}

export const deviceType = [
  {
    label: '网关子设备',
    value: 'childrenDevice',
  },
  {
    label: '直连设备',
    value: 'device',
  },
  {
    label: '网关设备',
    value: 'gateway',
  },
];

export const productTypeList = [
  {
    label: '直连设备',
    value: 'COMMON',
  },
  {
    label: '网关设备',
    value: 'GATEWAY',
  },
  {
    label: '网关子设备',
    value: 'SUBSET',
  },
  {
    label: '视频设备',
    value: 'VIDEO_COMMON',
  },
];

export const statusList = [
  {
    label: '启用',
    value: '0',
  },
  {
    label: '停用',
    value: '1',
  },
];

export const dataTypeList = [
  {
    label: 'JSON',
    value: 'JSON',
  }
];


export const protoTypeList = [
  {
    label: 'MQTT',
    value: 'MQTT',
  },
  {
    label: 'HTTP',
    value: 'HTTP',
  },
  {
    label: 'TCP',
    value: 'TCP',
  },
  {
    label: 'WEBSOCKET',
    value: 'WEBSOCKET',
  },
  {
    label: 'GB28181',
    value: 'GB28181',
  },
];

export const encryptMethodList = [
  {
    label: '明文',
    value: '0',
  },
  {
    label: 'SM4',
    value: '1',
  },
  {
    label: 'AES',
    value: '2',
  },
];

export let productTemplateList = [];

export const productModel = {
  id :'',
  //应用ID
  appId :'',
  //产品模版标识
  templateIdentification :'',
  //产品名称:自定义，支持中文、英文大小写、数字、下划线和中划线
  productName :'',
  //产品标识
  productIdentification :'',
  //支持以下两种产品类型•COMMON：普通产品，需直连设备。//•GATEWAY：网关产品，可挂载子设备。
  productType :'',
  //厂商ID:支持英文大小写，数字，下划线和中划线
  manufacturerId :'',
  //厂商名称 :支持中文、英文大小写、数字、下划线和中划线
  manufacturerName :'',
  //产品型号，建议包含字母或数字来保证可扩展性。支持英文大小写、数字、下划线和中划线
  model :'',
  //数据格式，默认为JSON无需修改。
  dataFormat :'',
  //设备类型:支持英文大小写、数字、下划线和中划线
  deviceType :'',
  //设备接入平台的协议类型，默认为MQTT无需修改。
  protocolType :'',
  encryptKey: '',
  encryptVector: '',
  //状态(字典值：0启用  1停用)
  status :'',
  //产品描述
  remark :'',
  //创建者
  createBy :'',
  //创建时间
  createTime :'',
  //更新者
  updateBy :'',
  //更新时间
  updateTime :'',
  //认证方式
  authMode :'',
  //用户名
  userName :'',
  //密码
  password :'',
  //连接实例
  connector :'',
  //签名密钥
  signKey :'',
  //协议加密方式
  encryptMethod :'',
}

// 设备接入
export function deviceAccessFormSchemas() {
  return [
    {
      field: 'appId',
      label: '应用场景',
      component: 'Input',
    },
    {
      field: 'deviceName',
      label: '设备名称',
      component: 'Input',
    },
    {
      field: `connectStatus`,
      label: `连接状态`,
      component: 'Select',
      componentProps: {
        options: [
          { value: '', label: '全部' },
          { value: 'ONLINE', label: '在线' },
          { value: 'OFFLINE', label: '离线' },
        ],
      },
      defaultValue: '',
    },
  ];
}
