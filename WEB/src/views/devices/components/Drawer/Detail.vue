<template>
  <div><Description layout="vertical" :column="2" :data="description" :schema="schema" /> </div>
</template>
<script lang="ts" setup>
import {onMounted, reactive} from 'vue';
import {Description} from '@/components/Description/index';
import {getDevicesInfo} from '@/api/device/devices';
import {useMessage} from '@/hooks/web/useMessage';
import moment from 'moment';
import {useRoute} from "vue-router";

const route = useRoute()

const { createMessage } = useMessage();
const description = reactive({
  id:'',
  clientId:'',
  appId:'',
  deviceIdentification:'',
  deviceName:'',
  deviceDescription:'',
  deviceStatus:'',
  connectStatus:'',
  isWill:'',
  productIdentification:'',
  createBy:'',
  createTime:'',
  updateBy:'',
  updateTime:'',
  remark:'',
  deviceVersion:'',
  deviceSn:'',
  ipAddress:'',
  macAddress:'',
  activeStatus:'',
  extension:'',
  activatedTime:'',
  lastOnlineTime:'',
});

const schema = [
  {
    field: 'appId',
    label: '应用场景',
  },
  {
    field: 'deviceName',
    label: '设备名称',
  },
  {
    field: 'deviceIdentification',
    label: '设备标识',
  },
  {
    field: 'deviceSn',
    label: '设备SN',
  },
  {
    field: 'productIdentification',
    label: '产品标识',
  },
  {
    field: 'connectStatus',
    label: '连接状态',
    render: (value) => (value === 'ONLINE' ? '在线' : '离线'),
  },
  {
    field: 'deviceVersion',
    label: '设备版本',
  },
  {
    field: 'ipAddress',
    label: 'IP地址',
  },
  {
    field: 'activeStatus',
    label: '激活状态',
    render: (value) => (value === 1 ? '已激活' : '未激活'),
  },
  {
    field: 'activatedTime',
    label: '激活时间',
    render: (value) => {
      if (value === null || value === '--') {
        return '--';
      } else {
        return moment(new Date(value))?.format?.('YYYY-MM-DD HH:mm:ss');
      }
    }
  },
  {
    field: 'lastOnlineTime',
    label: '最后上线时间',
    render: (value) => {
      if (value === null || value === '--') {
        return '--';
      } else {
        return moment(new Date(value))?.format?.('YYYY-MM-DD HH:mm:ss');
      }
    }
  },
  {
    field: 'deviceDescription',
    label: '设备描述',
  },
];

function copy(key) {
  const input = document.createElement('input');
  input.value = key;
  document.body.appendChild(input);
  input.select();
  document.execCommand('copy');
  document.body.removeChild(input);
  createMessage.success('复制成功');
}

const initDeviceDetail = async (record) => {
  const info = await getDevicesInfo(record?.id);
  // alert(JSON.stringify(info));
  Object.keys(description).forEach((item) => {
    description[item] = info.device[item] ?? '--';
  });
};

onMounted(() => {
  initDeviceDetail(route.params);
});
</script>

<style lang="less" scoped>
  :deep(.copy-warpper) {
    display: flex;
    align-items: center;

    .copy {
      margin-left: 10px;
      opacity: 0;
    }
  }

  :deep(.copy-warpper):hover .copy {
    opacity: 1;
  }
</style>
