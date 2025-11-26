<template>
  <div class="product-detail">
    <Description layout="vertical" :column="2" :data="descData" :schema="descSchema" />
  </div>
</template>
<script lang="ts" setup>
import {ref, watch} from 'vue';
import {deviceType, productTypeList, statusList} from '../Data.tsx';
import {Description} from '@/components/Description/index';

const props = defineProps({
  detail: {
    type: Object,
    require: true,
    default: () => ({}),
  },
});

const descData = ref({});
const descSchema = [
  {
    field: 'productName',
    label: '产品名称',
  },
  {
    field: 'productIdentification',
    label: '产品标识',
  },
  {
    field: 'templateIdentification',
    label: '模板标识',
  },
  {
    field: 'appId',
    label: '应用场景',
  },
  {
    field: 'productType',
    label: '产品类型',
    render: (target) => {
      let ret = productTypeList.find(item => item?.value == target)
      return ret?.label;
    }
  },
  {
    field: 'deviceType',
    label: '设备类型',
  },
  {
    field: 'authMode',
    label: '认证方式',
  },
  {
    field: 'userName',
    label: '用户名',
  },
  {
    field: 'password',
    label: '密码',
  },
  {
    field: 'connector',
    label: '连接实例',
  },
  {
    field: 'signKey',
    label: '签名密钥',
  },
  {
    field: 'encryptMethod',
    label: '协议加密方式',
    render: (target) => {
      return target == 0? '明文' : target == 2? 'AES' : 'SM2';
    }
  },
  {
    field: 'status',
    label: '状态',
    render: (target) => {
      let ret = statusList.find(item => item?.value == target)
      return ret?.label;
    }
  },
  {
    field: 'protocolType',
    label: '协议类型',
  },
  {
    field: 'dataFormat',
    label: '数据格式',
  },
  {
    field: 'manufacturerName',
    label: '厂商名称',
  },
  {
    field: 'remark',
    label: '描述',
  },
];

// function handlePreviewImage(img) {
//   if (!img) return;
//   createImgPreview({ imageList: [img] });
// }

function setDescripton(data) {
  descData.value = descSchema
    .map((item) => item.field)
    .reduce((p, c) => {
      p[c] = data[c] || '--';
      return p;
    }, {});
}
watch(
  () => props.detail,
  (newData) => {
    //alert(JSON.stringify(newData));
    setDescripton(newData);
  },
);
</script>

<style lang="less" scoped>
  :deep(.cl-image) {
    height: 50px;
    img {
      height: 100%;
    }
  }
</style>
