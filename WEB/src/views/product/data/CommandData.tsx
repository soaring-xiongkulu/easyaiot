import {BasicColumn} from '@/components/Table/src/types/table';
import {FormProps} from '@/components/Table';
import {FormActionType, FormSchema} from '@/components/Form/index';
import {Button, Space, Tooltip} from 'ant-design-vue';
import {PlusOutlined} from '@ant-design/icons-vue';
import {DebouncedFunc} from 'lodash-es';
import moment from "moment/moment";

type SchemasFn = {
  validateFields?: FormActionType['validateFields'];
  // 展示结构体参数
  btnClick?: (field: string) => void;
  // 编辑
  handleEdit?: (field: string, i: number) => void;
  // 删除
  handleDel?: (field: string, i: number) => void;
  // 数据类型切换
  handleChange?: (val: string) => void;
  list?: any[];
  isInner?: boolean;
  field?: string;
  disabled?: boolean;
  handleCheckSubuct?: (field: string) => Promise<void>;
};

// 单位下拉框选择列表
export const unitOptions = [
  {
    id: '0114dea5-28a3-459c-adda-5678637c5ee3',
    createTime: '2022-10-10 17:01:57',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '饱和度',
    itemValue: 'aw',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '043c6f88-1a52-400d-a256-58538d85fa0b',
    createTime: '2022-10-10 17:13:07',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '兆帕',
    itemValue: 'Mpa',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '0abfdc25-de57-44b2-81e6-1bee83b933c5',
    createTime: '2022-10-10 17:19:56',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '照度',
    itemValue: 'Lux',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '0c927ef7-0904-49cc-934b-036ce00182ea',
    createTime: '2022-10-10 17:49:27',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '卡路里',
    itemValue: 'cal',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '0ca25b2f-b774-426f-a6ad-a11718576fef',
    createTime: '2022-10-10 17:40:39',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '皮法',
    itemValue: 'pF',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '0cca664b-d45e-4bd5-845e-4ab5dadce085',
    createTime: '2022-10-10 17:57:13',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '平方毫米',
    itemValue: 'm㎡',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '0d43157e-db49-41e7-9db8-77f178636760',
    createTime: '2022-10-10 17:08:23',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千伏安',
    itemValue: 'kVA',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '0f823694-6be0-404a-9dae-6e98b8a534ca',
    createTime: '2022-10-10 17:57:04',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '平方厘米',
    itemValue: 'c㎡',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '0f8b088e-b899-4426-bbc8-ced98da0e1ad',
    createTime: '2022-10-10 17:54:24',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '摄氏度',
    itemValue: '°C',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '119918de-802b-41aa-a0be-65032dbb3562',
    createTime: '2022-10-10 17:55:46',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '升',
    itemValue: 'L',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '1893e812-8e1b-4444-89fa-c12193c51301',
    createTime: '2022-10-10 17:11:26',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '转每分钟',
    itemValue: 'r/min',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '1f309fd5-a0dd-4696-96ed-8793885ad7d9',
    createTime: '2022-10-10 17:54:55',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千帕',
    itemValue: 'kPa',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '204b28f6-8df7-4888-b452-c1a4d1f9a42e',
    createTime: '2022-10-10 17:04:56',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '血糖',
    itemValue: 'mmol/L',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '22e391ff-7b85-4e08-87f4-7e92fcbafb0e',
    createTime: '2022-10-10 17:40:50',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '微法',
    itemValue: 'μF',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '25646387-4a5c-40b2-bb18-4231c3f1b203',
    createTime: '2022-10-10 17:48:19',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '毫瓦',
    itemValue: 'mW',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '28802793-e61d-4b18-95b2-0fdb0a903ad8',
    createTime: '2022-10-10 17:06:22',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '档',
    itemValue: 'gear',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '28c2af6c-c6bd-4998-be9c-b9977d2c61e2',
    createTime: '2022-10-10 17:16:14',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '微克每平方分米每天',
    itemValue: 'μg/(d㎡·d)',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '2b8d1993-cc4f-41a2-b085-80e4fb16bb35',
    createTime: '2022-10-10 17:02:59',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '微克每升',
    itemValue: 'ppb',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '2ba611cd-6b72-4201-9f01-451941b40fd6',
    createTime: '2022-10-10 17:57:55',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '毫米',
    itemValue: 'mm',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '2d6d05a2-82a8-4028-8624-8c27563fe931',
    createTime: '2022-10-10 17:11:55',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '吨每小时',
    itemValue: 't/h',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '3236e1ed-d7e8-409d-9adc-7e7955240531',
    createTime: '2022-10-10 17:22:54',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '克每毫升',
    itemValue: 'g/mL',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '342e0524-b479-49ca-aee4-ccdbfa84a402',
    createTime: '2022-10-10 17:42:47',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '小时',
    itemValue: 'h',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '388a5adf-d4dd-48e4-af3b-074175a43004',
    createTime: '2022-10-10 17:22:19',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '百分比',
    itemValue: '%',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '3b4c2a2e-5d6c-427e-a921-ca2eedff5074',
    createTime: '2022-10-10 17:55:18',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '克',
    itemValue: 'g',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '3c987597-724d-4680-81ae-49a57607e7a6',
    createTime: '2022-10-10 17:14:25',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '微克每升',
    itemValue: 'μg/L',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '3e285acf-b42c-455e-b8b5-939d8464eeb3',
    createTime: '2022-10-10 17:43:15',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '月',
    itemValue: 'month',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '40c9e982-1a9e-4f06-b21b-41aae88d7c2d',
    createTime: '2022-10-10 17:58:32',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '米',
    itemValue: 'm',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '40e88dfb-a60a-4168-ab80-a74e92a23212',
    createTime: '2022-10-10 17:58:08',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '分米',
    itemValue: 'dm',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '41aba6c7-18e9-44df-b827-810a49b11b72',
    createTime: '2022-10-10 17:53:21',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '瓦时',
    itemValue: 'Wh',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '498858d5-4b8d-4a1f-b158-f9026eea900f',
    createTime: '2022-10-10 17:41:45',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '安培',
    itemValue: 'A',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '4b5773e5-633f-403e-bb9b-e650594420de',
    createTime: '2022-10-10 17:10:00',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '微瓦每平方厘米',
    itemValue: 'uw/cm2',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '4d51aeb1-2f0c-4493-852a-28161c828bb1',
    createTime: '2022-10-10 17:44:31',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '度',
    itemValue: '°',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '4d90e5b7-8323-4095-83c6-e68506e6c66d',
    createTime: '2022-10-10 17:00:20',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '浊度',
    itemValue: 'NTU',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '4fb3005b-25df-4bbf-8889-37813399c31f',
    createTime: '2022-10-10 17:56:13',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '立方毫米',
    itemValue: 'mm³',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '5290abd1-f4b3-4376-9f8f-ec3699750c91',
    createTime: '2022-10-10 17:57:24',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '平方千米',
    itemValue: 'k㎡',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '555f5dc4-7310-4c83-9543-94738f1a0223',
    createTime: '2022-10-10 17:21:46',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '分贝',
    itemValue: 'dB',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '57c234fe-29f2-4918-a3f3-c5a9121dfb0e',
    createTime: '2022-10-10 17:42:07',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '毫伏',
    itemValue: 'mV',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '57e3f0d0-c403-4bb3-a352-cc2ad2980368',
    createTime: '2022-10-10 17:19:37',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '百万分率',
    itemValue: 'ppm',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '5846f88b-e139-4fff-8117-030c93ec2210',
    createTime: '2022-10-10 17:53:56',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '华氏度',
    itemValue: '℉',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '592a8ab3-62d4-4b71-bbd9-76506f5a7ed0',
    createTime: '2022-10-10 17:42:16',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '伏特',
    itemValue: 'V',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '595e9e2b-9c7a-42ff-8c58-44b74f686846',
    createTime: '2022-10-10 17:15:43',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千字节',
    itemValue: 'KB',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '5dced094-68fc-4526-8ccb-7a711a389f1a',
    createTime: '2022-10-10 17:55:26',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千克',
    itemValue: 'kg',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '5de3d084-0476-4cab-8399-d47e8dfe1996',
    createTime: '2022-10-10 17:55:08',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '毫克',
    itemValue: 'mg',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '5ff1aa9a-41d2-4a86-abad-e8c22b1ac770',
    createTime: '2022-10-10 17:02:40',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '纳克每升',
    itemValue: 'ppt',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '6120b0a7-1103-4258-beeb-b49b1a7ef865',
    createTime: '2022-10-10 17:55:39',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '毫升',
    itemValue: 'mL',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '62ddbc36-94ed-42c2-a4d4-09e93b071a29',
    createTime: '2022-10-10 17:54:07',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '开尔文',
    itemValue: 'K',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '6320829f-5dfc-4d06-a17f-460c898029c8',
    createTime: '2022-10-10 17:08:56',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千乏',
    itemValue: 'kVar',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '63cfd81c-65f4-40b0-954f-8fb3ed4f3f91',
    createTime: '2022-10-10 17:10:34',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '立方米每秒',
    itemValue: 'm³/s',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '64011727-2c8a-4bac-ac57-a1db75227d18',
    createTime: '2022-10-10 17:48:41',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '瓦特',
    itemValue: 'W',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '6534fe87-7346-477e-a0f5-587bf8bcc987',
    createTime: '2022-10-10 17:44:40',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '弧度',
    itemValue: 'rad',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '65ef84a6-ffa3-4eeb-bc92-30ff7dea2ad4',
    createTime: '2022-10-10 17:13:18',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '立方米每小时',
    itemValue: 'm³/h',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '66db5749-35c1-416f-99d6-ef7df885b5f2',
    createTime: '2022-10-10 17:57:31',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '平方米',
    itemValue: '㎡',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '6b38abd4-70a5-4329-87f0-7714df0d7b33',
    createTime: '2022-10-10 17:53:08',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千瓦时',
    itemValue: 'kW·h',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '787f9b54-02d7-4541-995a-c69500b67eeb',
    createTime: '2022-10-10 17:41:34',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千安',
    itemValue: 'kA',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '7abd5937-8864-4265-92f1-99ff091a619e',
    createTime: '2022-10-10 17:22:38',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '比特',
    itemValue: 'bit',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '7b9db4ae-d22b-4bf0-a1e9-0b7751111672',
    createTime: '2022-10-10 17:47:53',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '赫兹',
    itemValue: 'Hz',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '7bcb278a-8832-4921-b677-acc1e5f14ffc',
    createTime: '2022-10-10 17:53:28',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '电子伏',
    itemValue: 'eV',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '8049564a-5d72-4ec9-9e5a-e4c1e7807b8a',
    createTime: '2022-10-10 16:57:57',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '毫克每千克',
    itemValue: 'mg/kg',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '86ee3c4e-db7d-496f-8f2c-b1b076d3cfa7',
    createTime: '2022-10-10 17:56:55',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '公顷',
    itemValue: 'h㎡',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '89049572-cb5b-4780-b751-82a0c3e84987',
    createTime: '2022-10-10 17:01:38',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '厘泊',
    itemValue: 'cP',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '8a2231e3-8665-4e83-90c2-be9d52f64256',
    createTime: '2022-10-10 17:39:47',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '克每立方米',
    itemValue: 'g/m³',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '8a2f6eb6-71e4-4b0b-82c7-5cef6f284e6c',
    createTime: '2022-10-10 17:11:13',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '公斤每秒',
    itemValue: 'kg/s',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '8ce55431-3f2d-4a7c-bd2d-68375600b40b',
    createTime: '2022-10-10 17:10:22',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '相对湿度',
    itemValue: '%RH',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '8e824280-13e0-43f0-9c87-3e2031bfb2e5',
    createTime: '2022-10-10 17:42:38',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '分钟',
    itemValue: 'min',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '8f4c7a77-7935-45c1-9b35-7d07d0274e0a',
    createTime: '2022-10-10 17:43:07',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '周',
    itemValue: 'week',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '92889058-4a78-48ef-bf49-0ced7d37680a',
    createTime: '2022-10-10 17:14:55',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '吉字节',
    itemValue: 'GB',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '9a672afa-cc19-4798-9e8a-fc1286d88892',
    createTime: '2022-10-10 17:02:27',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '巴',
    itemValue: 'bar',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '9c0b9a79-c434-4347-922c-ef60cfd03c0e',
    createTime: '2022-10-10 17:03:57',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '伏特每米',
    itemValue: 'V/m',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '9c72206c-b57a-40e7-ba36-2ebad445cc20',
    createTime: '2022-10-10 17:13:43',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千乏时',
    itemValue: 'kvarh',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '9f864e9f-2daa-4377-8636-7786c0c258c6',
    createTime: '2022-10-10 17:43:22',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '年',
    itemValue: 'year',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: '9fa8553d-e786-40df-b22e-5aec3f25f555',
    createTime: '2022-10-10 17:19:46',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '像素',
    itemValue: 'pixel',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'a1196d28-1e33-4c64-9530-614faa0e076e',
    createTime: '2022-10-10 17:39:34',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '毫克每立方米',
    itemValue: 'mg/m³',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'a3b3e1a7-c984-4216-9a59-6f31f2d42740',
    createTime: '2022-10-10 17:40:58',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '法拉',
    itemValue: 'F',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'a44cdbbf-c1c5-4a6b-abcf-4162c0b46c5f',
    createTime: '2022-10-10 17:04:18',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '滴速',
    itemValue: 'ml/min',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'a4ca7620-b84f-48d2-9dd1-9f1a67d37e39',
    createTime: '2022-10-10 17:54:15',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '吨',
    itemValue: 't',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'a5777103-138f-4aa0-880b-2674fa1c8077',
    createTime: '2022-10-10 17:15:55',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '字节',
    itemValue: 'B',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'a77ee52c-a4fd-487f-9d96-0dc72de5e119',
    createTime: '2022-10-10 17:39:58',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千克每立方米',
    itemValue: 'kg/m³',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'a892397d-881b-4c81-af9f-6b845f7d01c1',
    createTime: '2022-10-10 17:56:24',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '立方厘米',
    itemValue: 'cm³',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'b13fb9c9-0ae7-47e8-b1cb-468e82760631',
    createTime: '2022-10-10 17:44:24',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '分',
    itemValue: '′',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'b3ea89d7-6ac2-4362-995d-45d7fd8d0f13',
    createTime: '2022-10-10 17:55:02',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '帕斯卡',
    itemValue: 'Pa',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'b5c78bde-8617-4e91-93c2-8a041857cc0b',
    createTime: '2022-10-10 17:42:30',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '秒',
    itemValue: 's',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'b6b44ba6-af18-4d76-8b90-cfdf52068d35',
    createTime: '2022-10-10 17:01:13',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '降雨量',
    itemValue: 'mm/hour',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'b77e1272-2ccc-4f92-a1a0-85e5f81a2c07',
    createTime: '2022-10-10 17:57:39',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '纳米',
    itemValue: 'nm',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'b8ab363c-f94b-4a49-9704-da6f0cb4ec43',
    createTime: '2022-10-10 17:02:18',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '厘斯',
    itemValue: 'cst',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'b8eafc47-e9b3-4ba6-bafd-9f08b3a60b21',
    createTime: '2022-10-10 17:12:54',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '升每秒',
    itemValue: 'L/s',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'b97a5007-8de0-4f27-acd8-5d31566bd3a5',
    createTime: '2022-10-10 17:06:29',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '步',
    itemValue: 'stepCount',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'b9d62e8d-2e88-4c7b-b4cd-a577436d459e',
    createTime: '2022-10-10 17:06:41',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '标准立方米每小时',
    itemValue: 'Nm3/h',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'b9f513c1-d103-438b-9175-fb81cc8054d4',
    createTime: '2022-10-10 17:56:46',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '立方米',
    itemValue: 'm³',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'ba3b00e9-3a03-4e61-93bb-cfe69732c25f',
    createTime: '2022-10-10 17:05:38',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '次',
    itemValue: 'count',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'bc84bfdb-e8cf-4d71-b47d-4e226e3e0066',
    createTime: '2022-10-10 17:53:42',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千焦',
    itemValue: 'kJ',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'bf15dabe-592d-4e29-b93b-d02357f469d2',
    createTime: '2022-10-10 17:03:10',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '微西每厘米',
    itemValue: 'uS/cm',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'bf3c870e-f65d-4102-98a8-994888bfeb2b',
    createTime: '2022-10-10 17:02:05',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '个',
    itemValue: 'pcs',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'bf8d247d-6789-4581-bed4-703da6415ce7',
    createTime: '2022-10-10 17:48:06',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '微瓦',
    itemValue: 'μW',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'c078d658-5de5-41e9-88dd-d01dc52df2cf',
    createTime: '2022-10-10 17:21:10',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '重力加速度',
    itemValue: 'grav',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'c22c0369-554e-42c6-b3e7-cad0b3e13d0b',
    createTime: '2022-10-10 17:41:07',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '欧姆',
    itemValue: 'Ω',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'c31a9103-7270-40df-8a73-bbfcc507cb06',
    createTime: '2022-10-10 17:58:20',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千米',
    itemValue: 'km',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'c57f75cc-ad86-4f0a-bf6e-31ca5cb5b1d2',
    createTime: '2022-10-10 17:10:11',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '只',
    itemValue: '只',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'c69e5390-d72b-4e0a-9179-551255acfcbb',
    createTime: '2022-10-10 17:23:49',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '微克每立方米',
    itemValue: 'μg/m³',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'c6a4d58b-83e7-419d-9cfc-85b9dbd22fac',
    createTime: '2022-10-10 17:53:49',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '焦耳',
    itemValue: 'J',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'c83f40f8-2cb5-48c7-8864-ed8fb483d8c2',
    createTime: '2022-10-10 17:00:33',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: 'PH值',
    itemValue: 'pH',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'c916773c-d3a6-4efa-aeaa-19d71116b9b8',
    createTime: '2022-10-10 17:58:02',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '厘米',
    itemValue: 'cm',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'cc83ac66-1a07-4579-b16a-0cef60058d5e',
    createTime: '2022-10-10 17:14:37',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千卡路里',
    itemValue: 'kcal',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'd1b186db-d314-447d-82ed-f0499ee2e419',
    createTime: '2022-10-10 17:54:48',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '百帕',
    itemValue: 'hPa',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'd2e8ba80-bdc7-4672-8388-d48384ad410f',
    createTime: '2022-10-10 17:01:00',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '太阳总辐射',
    itemValue: 'W/㎡',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'd337ad07-1e62-46a2-931d-f91aab4539d3',
    createTime: '2022-10-10 17:44:11',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '秒',
    itemValue: '″',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'd490f7b4-eef0-4e52-872e-e250e18e7064',
    createTime: '2022-10-10 17:56:36',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '立方千米',
    itemValue: 'km³',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'd670cb2b-f2a7-48c9-9b4a-95661c6b2cd0',
    createTime: '2022-10-10 17:40:14',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '纳法',
    itemValue: 'nF',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'e231542e-5cb7-4f73-a952-84bfcf1b4f10',
    createTime: '2022-10-10 17:54:35',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '毫帕',
    itemValue: 'mPa',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'e268cd01-6662-4dbb-800c-a33f0375f225',
    createTime: '2022-10-10 17:04:45',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '血压',
    itemValue: 'mmHg',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'e3df9f96-2228-4af1-ba49-eb8cfe8739ed',
    createTime: '2022-10-10 17:01:25',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '乏',
    itemValue: 'var',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'e3e0fa34-2e00-4aa4-afbd-14f716988da7',
    createTime: '2022-10-10 17:43:41',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千米每小时',
    itemValue: 'km/h',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'e4ad393f-18ef-48b1-929d-9e61891fe3e5',
    createTime: '2022-10-10 17:12:38',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千卡每小时',
    itemValue: 'KCL/h',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'e6b32180-afbb-4057-b320-5e7fc6305b4f',
    createTime: '2022-10-10 17:48:29',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千瓦特',
    itemValue: 'kW',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'ee405f67-2237-44dd-b0ba-fae53055f150',
    createTime: '2022-10-10 17:05:10',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '毫米每秒',
    itemValue: 'mm/s',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'ef7d4a55-4ff8-4519-82e4-c7b940cfd5db',
    createTime: '2022-10-10 17:08:13',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '千伏',
    itemValue: 'kV',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'f360ef69-5e0f-431c-837e-c7a145ce5a9b',
    createTime: '2022-10-10 17:42:23',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '毫秒',
    itemValue: 'ms',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'f39300a0-1a39-485d-9066-b9efb77ea891',
    createTime: '2022-10-10 17:23:08',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '克每升',
    itemValue: 'g/L',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'f3d60370-54af-467b-ae65-b9711f0733ee',
    createTime: '2022-10-10 17:43:58',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '米每秒',
    itemValue: 'm/s',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'f3e394fc-cd9a-4553-8492-b4bb6912b779',
    createTime: '2022-10-10 17:41:24',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '毫安',
    itemValue: 'mA',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'f542aba9-be32-4a52-839f-fda661d77cf8',
    createTime: '2022-10-10 17:41:17',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '微安',
    itemValue: 'μA',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'f58c1c20-f902-4246-b8f5-930ddb3ae4a6',
    createTime: '2022-10-10 17:15:33',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '兆字节',
    itemValue: 'MB',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'f5ef2d86-2846-45af-be08-2f2c3058376f',
    createTime: '2022-10-10 17:05:19',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '转每分钟',
    itemValue: 'turn/m',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'f6e0d263-fc71-42cc-86a4-809a409ced59',
    createTime: '2022-10-10 17:43:29',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '节',
    itemValue: 'kn',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'f7d95da9-20f3-4b54-a907-fc1eb34f47c8',
    createTime: '2022-10-10 17:57:47',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '微米',
    itemValue: 'μm',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'f805ba0f-668e-4461-8423-29b0ab68041c',
    createTime: '2022-10-10 17:23:20',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '毫克每升',
    itemValue: 'mg/L',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'fac8fdb5-76f8-4eee-b3f3-44a3ed2c87fe',
    createTime: '2022-10-10 17:55:33',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '牛',
    itemValue: 'N',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'fb28cd0a-d388-423f-8fb2-8a38f5aa317f',
    createTime: '2022-10-10 17:43:00',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '日',
    itemValue: 'day',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'fbed00f6-c8c2-45a5-b39c-4db9f405b4f1',
    createTime: '2022-10-10 17:03:22',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '牛顿每库仑',
    itemValue: 'N/C',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'fe1e6b60-a97c-4804-a0ef-cfbe824043ab',
    createTime: '2022-10-10 17:22:29',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '流明',
    itemValue: 'lm',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
  {
    id: 'ff2b6eb0-d01c-4a51-a892-e7695f12f19a',
    createTime: '2022-10-10 17:00:45',
    dictId: '4ff6a81a-3945-4fec-a9d8-f74c9a1554a7',
    itemText: '土壤EC值',
    itemValue: 'dS/m',
    sort: 1,
    status: 1,
    sysDict: { dictName: '属性单位', dictCode: 'attribute_unit' },
  },
];

export const dataTypeOptions = [
  {
    label: 'in32（整数型）',
    value: 'INT',
    isInner: true,
  },
  {
    label: 'double（双精度浮点型）',
    value: 'DOUBLE',
    isInner: true,
  },
  {
    label: 'bool（布尔型）',
    value: 'BOOL',
    isInner: true,
  },
  {
    label: 'text（字符串）',
    value: 'TEXT',
    isInner: true,
  },
];

// 功能类型tabs切换
export const tabsOptions = [
  {
    label: '属性',
    key: 'properties',
  },
  {
    label: '服务',
    key: 'services',
  },
  {
    label: '事件',
    key: 'events',
  },
];

export const getCommandBasicColumns = (functionType : String): BasicColumn[] => {
  return [
    {
      title: '指示命令编码',
      dataIndex: 'commandCode',
      width: 100,
    },
    {
      title: '指示命令名称',
      dataIndex: 'name',
      width: 100,
    },
    {
      title: '命令描述',
      dataIndex: 'description',
      width: 100,
    },
    {
      title: '备注',
      dataIndex: 'remark',
      width: 100,
    },
    {
      title: '创建时间',
      dataIndex: 'createTime',
      customRender({ value }) {
        const newDate = new Date(value);
        const _val = moment(newDate)?.format?.('YYYY-MM-DD HH:mm:ss') ?? value;
        return (
          <Tooltip title={_val}>
            <span class={'ellipsis-span'}>{_val ?? '--'}</span>
          </Tooltip>
        );
      },
      ellipsis: true,
      width: 100,
    }
  ];
};

export function getCommandFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 90,
    baseColProps: { span: 8 },
    schemas: [
      {
        field: `name`,
        label: `指示命令名称`,
        component: 'Input',
      },
      {
        field: `commandCode`,
        label: `指示命令编码`,
        component: 'Input',
      },
    ],
  };
}

export const EditFormSchemas = (
  checkIdentifier:
    | false
    | DebouncedFunc<(val: string) => Promise<void>>
    | ((val: string) => Promise<void>),
  functionType:
    | false
    | string,
): FormSchema[] => {
  return [];
};

export const IntFormSchemas = ({ validateFields }: SchemasFn): FormSchema[] => {
  const temp = [
    {
      field: 'min',
      label: '取值范围',
      component: 'InputNumber',
      colProps: {
        span: 12,
      },
      componentProps: {
        step: 1,
        stringMode: true,
      },
      dynamicRules: ({ model }) => {
        const max = model['max'];
        return [
          {
            validator(_, value) {
              if (parseFloat(value) >= parseFloat(max)) return Promise.reject('最大值小于最小值');
              return Promise.resolve();
            },
          },
        ];
      },
    },
    {
      field: 'max',
      label: '~',
      component: 'InputNumber',
      colProps: {
        span: 12,
      },
      componentProps: {
        step: 1,
        onchange() {
          validateFields && validateFields(['rangeMin']);
        },
        stringMode: true,
      },
      labelWidth: '20px',
    },
    {
      field: 'step',
      label: '步长',
      component: 'InputNumber',
      colProps: {
        span: 24,
      },
      componentProps: {
        step: 1,
        parser(val) {
          return parseInt(val);
        },
      },
      dynamicRules: ({ model }) => {
        const max = model['rangeMax'];
        return [
          {
            validator(_, value) {
              if (value > max) return Promise.reject('步长不能大于取值范围的差值');
              return Promise.resolve();
            },
            trigger: 'change',
          },
        ];
      },
    },
    {
      field: 'unit',
      label: '单位',
      component: 'Select',
      colProps: {
        span: 24,
      },
      componentProps: {
        options: unitOptions.map((e) => {
          return {
            ...e,
            label: e.itemText,
            value: e.itemValue,
          };
        }),
      },
    },
  ].reverse();

  return temp as FormSchema[];
};

export const BoolFormSchemas = (): FormSchema[] => {
  return [
    {
      field: 'boolOpen',
      label: '1 - ',
      component: 'Input',
      colProps: {
        span: 24,
      },
      dynamicRules({ model }) {
        const close = model['boolClose'];
        return [
          {
            trigger: ['change', 'blur'],
            validator(_, value) {
              if (!value) return Promise.reject("'boolOpen' is required");
              if (value === close) return Promise.reject('布尔值不能相同');
              return Promise.resolve();
            },
            required: true,
          },
        ];
      },
      componentProps: {
        defaultValue: 'on',
        placeholder: '如：on',
      },
      defaultValue: 'on'
    },
    {
      field: 'boolClose',
      label: '0 - ',
      component: 'Input',
      colProps: {
        span: 24,
      },
      dynamicRules({ model }) {
        //alert(JSON.stringify(model));
        const open = model['boolOpen'];
        return [
          {
            trigger: ['change', 'blur'],
            validator(_, value) {
              if (!value) return Promise.reject("'boolClose' is required");
              if (value === open) return Promise.reject('布尔值不能相同');
              return Promise.resolve();
            },
            required: true,
          },
        ];
      },
      componentProps: {
        defaultValue: 'off',
        placeholder: '如：off',
      },
      defaultValue: 'off'
    },
  ];
};

export const TextFormSchemas = (): FormSchema[] => {
  const temp: FormSchema[] = [
    {
      field: 'maxlength',
      label: '数据长度',
      component: 'Input',
      colProps: {
        span: 24,
      },
      componentProps: {
        defaultValue: '10240',
      },
      renderComponentContent() {
        return {
          suffix: () => '字节',
        };
      },
      defaultValue: '10240',
    },
  ];

  return temp;
};

// 结构体参数渲染函数
export const SubuctRender = ({
  btnClick,
  handleEdit,
  list,
  field = '',
  handleDel,
  disabled = false,
}: SchemasFn) => {
  const handleClick = () => {
    btnClick?.(field);
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      {list?.map((e, i) => {
        return (
          <Space class={'alert'}>
            <span style={{ color: '#6b7280' }}>参数名称：{e.propertyName}</span>

            <div class={'options'}>
              <Button type="link" onClick={() => handleEdit?.(field, i)}>
                {disabled ? '查看' : '编辑'}
              </Button>
              <Button type="link" onClick={() => handleDel?.(field, i)} disabled={disabled}>
                删除
              </Button>
            </div>
          </Space>
        );
      })}
      <Button type="link" onClick={() => handleClick()} disabled={disabled}>
        <PlusOutlined class={'app-iconify'} />
        增加参数
      </Button>
    </Space>
  );
};

export const SubuctSchemas = ({ btnClick, list, handleCheckSubuct }: SchemasFn): FormSchema[] => {
  return [
    {
      field: 'innerJson',
      label: 'JSON对象',
      component: 'Input',
      colProps: {
        span: 24,
      },
      render({ field }) {
        return SubuctRender({ btnClick, list, field });
      },
      // rules: [{ required: true, message: 'JSON对象不能为空', trigger: 'change' }],
      dynamicRules({ field }) {
        return [
          {
            validator(_, _value, cb) {
              handleCheckSubuct &&
                handleCheckSubuct(field)
                  .then(() => {
                    cb();
                  })
                  .catch(() => {
                    cb('JSON对象不能为空');
                  });
            },
            trigger: 'change',
          },
        ];
      },
    },
  ];
};

// 属性
export const PropsSchemas = ({ handleChange, isInner }: SchemasFn): FormSchema[] => {
  return [
    {
      field: 'datatype',
      label: '数据类型',
      component: 'Select',
      rules: [{ required: true, message: '请选择数据类型', trigger: 'change' }],
      colProps: {
        span: 24,
      },
      componentProps: {
        options: dataTypeOptions.filter((e) => {return !isInner || e.isInner === isInner}),
        onChange(val) {
          handleChange && handleChange(val);
        },
        defaultValue: 'INT',
        allowClear: false,
      },
      defaultValue: 'INT',
    },
    {
      field: 'method',
      label: '读写类型',
      component: 'RadioGroup',
      rules: [{ required: true, message: '请选择读写类型', trigger: 'change' }],
      colProps: {
        span: 24,
      },
      componentProps: {
        defaultValue: 'r',
        options: [
          {
            label: '读写',
            value: 'w',
          },
          {
            label: '只读',
            value: 'r',
          },
        ],
      },
      defaultValue: 'r',
    },
    {
      field: 'description',
      label: '备注',
      component: 'InputTextArea',
      colProps: {
        span: 24,
      },
      componentProps: {
        rows: 4,
      },
    },
    {
      field: 'propertyCode',
      label: '属性标识',
      component: 'Input',
      rules: [{ required: true, message: '请输入标识符', trigger: 'change' }],
      colProps: {
        span: 24,
      },
      // dynamicRules() {
      //   if (!checkIdentifier)
      //     return [{ required: true, message: '请输入标识符', trigger: 'change' }];
      //
      //   return [
      //     {
      //       validator(_, value, cb) {
      //         if (!value) return cb('请输入标识符');
      //
      //         (checkIdentifier(value) as unknown as Promise<void>)
      //           .then(() => {
      //             cb();
      //           })
      //           .catch(() => {
      //             cb('标识符重复，请重新输入');
      //           });
      //       },
      //       trigger: 'change',
      //     },
      //   ];
      // },
    },
    {
      field: 'propertyName',
      label: '属性名称',
      component: 'Input',
      rules: [{ required: true, message: '请输入名称', trigger: 'change' }],
      colProps: {
        span: 24,
      },
    },
  ];
};

// 服务
export const ServerSchemas = ({ btnClick, list, handleCheckSubuct }: SchemasFn): FormSchema[] => {
  return [
    // {
    //   field: 'inputParams',
    //   label: '输入参数',
    //   component: 'Input',
    //   colProps: {
    //     span: 24,
    //   },
    //   render({ field }) {
    //     return SubuctRender({ btnClick, list, field });
    //   },
    //   // rules: [{ required: true, message: 'JSON对象不能为空', trigger: 'change' }],
    //   dynamicRules({ field }) {
    //     return [
    //       {
    //         validator(_, _value, cb) {
    //           handleCheckSubuct &&
    //           handleCheckSubuct(field)
    //             .then(() => {
    //               cb();
    //             })
    //             .catch(() => {
    //               cb('JSON对象不能为空');
    //             });
    //         },
    //         trigger: 'change',
    //       },
    //     ];
    //   },
    // },
    // {
    //   field: 'outParams',
    //   label: '输出参数',
    //   component: 'Input',
    //   colProps: {
    //     span: 24,
    //   },
    //   render({ field }) {
    //     return SubuctRender({ btnClick, list, field });
    //   },
    //   // rules: [{ required: true, message: 'JSON对象不能为空', trigger: 'change' }],
    //   dynamicRules({ field }) {
    //     return [
    //       {
    //         validator(_, _value, cb) {
    //           handleCheckSubuct &&
    //           handleCheckSubuct(field)
    //             .then(() => {
    //               cb();
    //             })
    //             .catch(() => {
    //               cb('JSON对象不能为空');
    //             });
    //         },
    //         trigger: 'change',
    //       },
    //     ];
    //   },
    // },
    {
      field: 'description',
      label: '备注',
      component: 'InputTextArea',
      colProps: {
        span: 24,
      },
      componentProps: {
        rows: 4,
      },
    },
    {
      field: 'serviceCode',
      label: '服务标识',
      component: 'Input',
      rules: [{ required: true, message: '请输入标识符', trigger: 'change' }],
      colProps: {
        span: 24,
      },
      // dynamicRules() {
      //   if (!checkIdentifier)
      //     return [{ required: true, message: '请输入标识符', trigger: 'change' }];
      //
      //   return [
      //     {
      //       validator(_, value, cb) {
      //         if (!value) return cb('请输入标识符');
      //
      //         (checkIdentifier(value) as unknown as Promise<void>)
      //           .then(() => {
      //             cb();
      //           })
      //           .catch(() => {
      //             cb('标识符重复，请重新输入');
      //           });
      //       },
      //       trigger: 'change',
      //     },
      //   ];
      // },
    },
    {
      field: 'serviceName',
      label: '服务名称',
      component: 'Input',
      rules: [{ required: true, message: '请输入名称', trigger: 'change' }],
      colProps: {
        span: 24,
      },
    },
  ];
};

// 事件
export const EventSchemas = ({ btnClick, list, handleCheckSubuct }: SchemasFn): FormSchema[] => {
  return [
    // {
    //   field: 'outParams',
    //   label: '输出参数',
    //   component: 'Input',
    //   colProps: {
    //     span: 24,
    //   },
    //   render({ field }) {
    //     return SubuctRender({ btnClick, list, field });
    //   },
    //   // rules: [{ required: true, message: 'JSON对象不能为空', trigger: 'change' }],
    //   dynamicRules({ field }) {
    //     return [
    //       {
    //         validator(_, _value, cb) {
    //           handleCheckSubuct &&
    //           handleCheckSubuct(field)
    //             .then(() => {
    //               cb();
    //             })
    //             .catch(() => {
    //               cb('JSON对象不能为空');
    //             });
    //         },
    //         trigger: 'change',
    //       },
    //     ];
    //   },
    // },
    {
      field: 'eventType',
      label: '事件类型',
      component: 'RadioGroup',
      rules: [{ required: true, message: '请选择事件类型', trigger: 'change' }],
      colProps: {
        span: 24,
      },
      componentProps: {
        options: [
          {
            label: '信息',
            value: 'INFO_EVENT_TYPE',
          },
          {
            label: '告警',
            value: 'ALERT_EVENT_TYPE',
          },
          {
            label: '故障',
            value: 'ERROR_EVENT_TYPE',
          },
        ],
      },
      defaultValue: 'INFO_EVENT_TYPE',
    },
    {
      field: 'description',
      label: '备注',
      component: 'InputTextArea',
      colProps: {
        span: 24,
      },
      componentProps: {
        rows: 4,
      },
    },
    {
      field: 'eventCode',
      label: '事件标识',
      component: 'Input',
      rules: [{ required: true, message: '请输入标识符', trigger: 'change' }],
      colProps: {
        span: 24,
      },
    },
    {
      field: 'eventName',
      label: '事件名称',
      component: 'Input',
      rules: [{ required: true, message: '请输入名称', trigger: 'change' }],
      colProps: {
        span: 24,
      },
    },
  ];
};
