<template>
  <div class="device-drawer-warpper" style="height: 100%">
    <Card class="detail-info">
      <div class="ant-card">
        <div class="ant-card-body">
          <div class="device_title">
            <div><span>{{ description.deviceName }}</span></div>
          </div>
          <div class="base_data">
            <div class="item"><span>状态：</span><span
              :class="description.connectStatus == 'ONLINE'? 'green' : 'red'">{{
                description.connectStatus == "ONLINE" ? "在线" : "离线"
              }}</span>
            </div>
            <div class="item"><span>应用场景：</span><span>{{ description.appId }}</span></div>
            <div class="item"><span>产品名称：</span><span>{{ description.productName }}</span></div>
            <div class="item">
              <span>设备标识：</span><span>{{ description.deviceIdentification }}</span></div>
            <div class="item"><span>连接实例：</span><span>{{ description.connector }}</span></div>
            <div class="item"><span>用户名：</span><span>{{ description.userName }}</span></div>
            <div class="item"><span>密码：</span><span>{{ description.password }}</span></div>
            <div class="item"><span>厂商名称：</span><span>{{ description.manufacturerName }}</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
    <Card class="device-tabs" ref="cardRef">
      <Tabs v-model:activeKey="activeKey">
        <TabPane v-for="item in tabPaneList" :key="item.componentName" :tab="item.label">
          <component :is="item.component" module="DEVICE"/>
        </TabPane>
      </Tabs>
    </Card>
  </div>
</template>
<script setup lang="ts">
import {defineEmits, markRaw, onMounted, reactive, ref} from 'vue';
import {TabPane, Tabs} from 'ant-design-vue';
import {TingModel} from '@/components/EditDrawer';
import Detail from './Detail.vue';
import {useRoute} from "vue-router";
import {getDevicesInfo} from "@/api/device/devices";

defineOptions({name: 'DeviceDetail'})

const description = reactive({
  id: '',
  clientId: '',
  appId: '',
  deviceIdentification: '',
  deviceName: '',
  deviceDescription: '',
  deviceStatus: '',
  connectStatus: '',
  isWill: '',
  productIdentification: '',
  createBy: '',
  createTime: '',
  updateBy: '',
  updateTime: '',
  remark: '',
  deviceVersion: '',
  deviceSn: '',
  ipAddress: '',
  macAddress: '',
  activeStatus: '',
  extension: '',
  activatedTime: '',
  lastOnlineTime: '',
  productName: '',
  manufacturerName: '',
  deviceType: "",
  protocolType: "",
  connector: "",
  userName: "",
  password: "",
});

const route = useRoute()

const emits = defineEmits(['success', 'register']);

const initDeviceDetail = async (record) => {
  const info = await getDevicesInfo(record?.id);
  Object.keys(description).forEach((item) => {
    description[item] = info.device[item] ?? info.product[item] ?? '--';
  });
};

onMounted(() => {
  initDeviceDetail(route.params);
});

const activeKey = ref('Detail');
const tabPaneList = reactive([
  {label: '基础信息', componentName: 'Detail', component: markRaw(Detail)},
  {label: '运行状态', componentName: 'TingModel', component: markRaw(TingModel)},
]);
</script>
<style lang="less" scoped>
.device-drawer-warpper {
  overflow-y: hidden;

  .detail-info {
    margin-bottom: 20px;
  }

  .ant-card {
    box-sizing: border-box;
    padding: 0;
    color: #000000d9;
    font-size: 14px;
    font-variant: tabular-nums;
    line-height: 1.5715;
    list-style: none;
    font-feature-settings: tnum;
    position: relative;
    background: #fff;
    border-radius: 2px;
    margin: 16px 16px 0;

    .ant-card-body {
      padding: 24px;

      .device_title {
        height: 32px;
        font-size: 16px;
        font-weight: 600;
        color: #2e3033;
        line-height: 19px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;

        .ant-btn {
          line-height: 1.5715;
          position: relative;
          display: inline-block;
          font-weight: 400;
          white-space: nowrap;
          text-align: center;
          background-image: none;
          border: 1px solid transparent;
          box-shadow: 0 2px #00000004;
          cursor: pointer;
          transition: all .3s cubic-bezier(.645, .045, .355, 1);
          -webkit-user-select: none;
          -moz-user-select: none;
          user-select: none;
          touch-action: manipulation;
          height: 32px;
          padding: 4px 15px;
          font-size: 14px;
          border-radius: 2px;
          color: #000000d9;
          border-color: #d9d9d9;
          background: #fff;
        }

        .ant-btn-primary {
          color: #fff;
        }

        .ant-btn-dangerous.ant-btn-primary {
          border-color: #ff4d4f;
          background: #ff4d4f;
          text-shadow: 0 -1px 0 rgba(0, 0, 0, .12);
          box-shadow: 0 2px #0000000b;
        }
      }

      .base_data {
        display: flex;
        align-items: center;
        font-size: 12px;
        color: #a6a6a6;
        line-height: 17px;

        .item:first-child {
          border-left: 0;
        }

        .item {
          padding-left: 12px;
          padding-right: 12px;
          border-left: 1px solid #e0e0e0;

          .red {
            color: #fa3758;
          }
        }
      }
    }
  }

  .device-tabs {
    .ant-tabs {
      background-color: #FFFFFF;
      padding: 20px;
      padding-top: 10px;
      margin: 16px 19px 0 15px;
    }
  }
}
</style>
