<template>
  <div class="device-drawer-wrapper">
    <!-- 设备基本信息卡片 -->
    <Card class="detail-info">
      <div class="device_title">
        <div><span>{{ description.deviceName }}</span></div>
      </div>
      <div class="base_data">
        <div class="item">
          <span>状态：</span>
          <span :class="description.connectStatus == 'ONLINE' ? 'green' : 'red'">
            {{ description.connectStatus == "ONLINE" ? "在线" : "离线" }}
          </span>
        </div>
        <div class="item"><span>应用场景：</span><span>{{ description.appId }}</span></div>
        <div class="item"><span>产品名称：</span><span>{{ description.productName }}</span></div>
        <div class="item"><span>设备标识：</span><span>{{ description.deviceIdentification }}</span></div>
        <div class="item"><span>连接实例：</span><span>{{ description.connector }}</span></div>
        <div class="item"><span>用户名：</span><span>{{ description.userName }}</span></div>
        <div class="item"><span>密码：</span><span>{{ description.password }}</span></div>
        <div class="item"><span>厂商名称：</span><span>{{ description.manufacturerName }}</span></div>
      </div>
    </Card>

    <!-- Tab 内容卡片 -->
    <Card class="device-tabs-card">
      <Tabs 
        v-model:activeKey="activeKey"
        :animated="{ inkBar: true, tabPane: true }"
        :tabBarGutter="80"
        @tabClick="handleTabClick"
      >
        <TabPane key="Detail" tab="基础信息">
          <Detail />
        </TabPane>

        <TabPane key="TingModel" tab="运行状态">
          <TingModel />
        </TabPane>

        <TabPane key="Shadow" tab="设备影子">
          <Shadow />
        </TabPane>

        <TabPane key="Event" tab="事件日志">
          <Event />
        </TabPane>

        <TabPane key="Service" tab="指令日志">
          <Service />
        </TabPane>

        <TabPane key="DeviceLog" tab="设备日志">
          <DeviceLog />
        </TabPane>

        <TabPane key="Topic" tab="Topic管理">
          <Topic />
        </TabPane>
      </Tabs>
    </Card>
  </div>
</template>
<script setup lang="ts">
import {onMounted, reactive, ref} from 'vue';
import {Card, TabPane, Tabs} from 'ant-design-vue';
import TingModel from '../Model/index.vue';
import Detail from './Detail.vue';
import Shadow from '../Shadow/index.vue';
import Event from '../Event/index.vue';
import Service from '../Service/index.vue';
import DeviceLog from '../DeviceLog/index.vue';
import Topic from '../Topic/index.vue';
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

const handleTabClick = (key) => {
  activeKey.value = key;
};
</script>
<style lang="less" scoped>
.device-drawer-wrapper {
  height: 100%;
  overflow-y: auto;
  background: #f5f7fa;
  padding: 20px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;

  // 设备基本信息卡片
  .detail-info {
    margin-bottom: 16px;

    :deep(.ant-card-body) {
      padding: 20px 24px;
    }

    .device_title {
      min-height: 32px;
      font-size: 16px;
      font-weight: 600;
      color: #1a1a1a;
      line-height: 1.5;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-bottom: 12px;
      border-bottom: 1px solid #f0f0f0;

      span {
        display: flex;
        align-items: center;
        gap: 12px;
      }
    }

    .base_data {
      display: flex;
      align-items: center;
      flex-wrap: nowrap;
      gap: 0;
      font-size: 13px;
      color: #666;
      line-height: 1.6;
      overflow-x: auto;
      padding-bottom: 4px;

      &::-webkit-scrollbar {
        height: 4px;
      }

      &::-webkit-scrollbar-thumb {
        background: #d9d9d9;
        border-radius: 2px;
      }

      .item:first-child {
        border-left: none;
        padding-left: 0;
      }

      .item {
        padding-left: 20px;
        padding-right: 20px;
        border-left: 1px solid #e8e8e8;
        flex: 0 0 auto;
        white-space: nowrap;

        span:first-child {
          color: #999;
          font-weight: 400;
          margin-right: 6px;
          font-size: 13px;
        }

        span:last-child {
          color: #1a1a1a;
          font-weight: 500;
          font-size: 13px;
        }

        .red {
          color: #ff4d4f;
          font-weight: 500;
        }

        .green {
          color: #52c41a;
          font-weight: 500;
        }
      }
    }
  }

  // Tab 卡片
  .device-tabs-card {
    margin: 0;
    background: #ffffff;
    border-radius: 8px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
    border: 1px solid rgba(0, 0, 0, 0.06);
    overflow: hidden;
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    
    :deep(.ant-card-body) {
      padding: 0;
      background: #ffffff;
      flex: 1;
      display: flex;
      flex-direction: column;
      min-height: 0;
    }
    
    :deep(.ant-tabs) {
      background-color: #ffffff;
      padding: 8px 20px;
      margin: 0;
      flex: 1;
      display: flex;
      flex-direction: column;
      min-height: 0;
    }
    
    :deep(.ant-tabs-nav) {
      margin-bottom: 4px;
      padding: 0;
      background: #ffffff;
      flex-shrink: 0;
    }
    
    :deep(.ant-tabs-content-holder) {
      padding: 0 16px 12px;
      background: #ffffff;
      flex: 1;
      min-height: 0;
      overflow: hidden;
    }
    
    :deep(.ant-tabs-content) {
      height: 100%;
    }
    
    :deep(.ant-tabs-tabpane) {
      padding: 0;
      
      > * {
        height: 100%;
        overflow-y: auto;
      }
    }
    
    :deep(.ant-tabs-tab) {
      padding: 8px 16px;
      font-size: 14px;
      font-weight: 500;
      color: #666;
      transition: all 0.3s ease;
      margin-right: 4px;

      &:hover {
        color: #1890ff;
      }
    }
    
    :deep(.ant-tabs-tab-active) {
      .ant-tabs-tab-btn {
        color: #1890ff;
        font-weight: 600;
      }
    }

    :deep(.ant-tabs-ink-bar) {
      height: 3px;
      border-radius: 2px;
    }
  }
}

</style>
