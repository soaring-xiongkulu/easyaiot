<!-- eslint-disable vue/v-on-event-hyphenation -->
<template>
  <div class="product-drawer-warpper" style="height: 100%">
    <Card class="detail-info">
      <div class="ant-card">
        <div class="ant-card-body">
          <div class="device_title">
            <div><span>{{ state.record.productName }}</span></div>
          </div>
          <div class="base_data">
            <div class="item"><span>状态：</span><span
              :class="state.record.status == '0'? 'green' : 'red'">{{
                state.record.status == '0' ? "启用" : "禁用"
              }}</span>
            </div>
            <div class="item"><span>应用场景：</span><span>{{ state.record.appId }}</span></div>
            <div class="item"><span>产品名称：</span><span>{{ state.record.productName }}</span>
            </div>
            <div class="item">
              <span>产品标识：</span><span>{{ state.record.productIdentification }}</span></div>
            <div class="item">
              <span>模板标识：</span><span>{{ state.record.templateIdentification }}</span></div>
            <div class="item"><span>用户名：</span><span>{{ state.record.userName }}</span></div>
            <div class="item"><span>密码：</span><span>{{ state.record.password }}</span></div>
            <div class="item"><span>厂商名称：</span><span>{{ state.record.manufacturerName }}</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
    <Card class="product-tabs" ref="cardRef">
      <Tabs
        :animated="{ inkBar: true, tabPane: true }"
        :activeKey="state.activeKey"
        :tabBarGutter="80"
        @tabClick="handleTabClick"
      >
        <TabPane key="1" tab="基础信息">
          <ProductDetail :detail="state.record"/>
        </TabPane>
        <TabPane key="3" tab="模型定义">
          <PhsyicalModal
            :product-identification="state.record.productIdentification"
            :device-profile-name="state.record.productName"
            :template-identification="state.record.templateIdentification"
          />
        </TabPane>
      </Tabs>
    </Card>
  </div>
</template>
<script lang="ts" setup>
import {onMounted, reactive} from 'vue';
import {TabPane, Tabs} from 'ant-design-vue';
import ProductDetail from './ProductDetail.vue';
import PhsyicalModal from './PhsyicalModal.vue';
import {productModel} from "@/views/product/Data";
import {getDeviceProfileDetail} from "@/api/device/product";
import {useRoute} from 'vue-router'

defineOptions({name: 'ProductDetail'})

const route = useRoute()

const emits = defineEmits(['upload:list']);

const state = reactive({
  id: '',
  activeKey: '1',
  record: productModel
});

async function initProductDetail(record) {
  try {
    state.record.id = record.id;
    state.record.templateIdentification = record.templateIdentification
    state.record.productIdentification = record.productIdentification
    const ret = await getDeviceProfileDetail(record.id);
    state.record = ret;
    //console.log("state.record...", record);
    // getProductImage(ret.image);
    // //console.log('state.record.imageData ...', state.record.imageData);
  } catch (error) {
    console.error(error)
    //console.log('getProductDetail ...', error);
  }
}

const handleTabClick = (activeKey) => {
  state.activeKey = activeKey;
};

onMounted(() => {
  initProductDetail(route.params);
})
</script>

<style lang="less" scoped>
:deep(.product-drawer .scrollbar__wrap) {
  overflow: hidden;
}

:deep(.product-drawer .is-vertical) {
  display: none;
}

.product-drawer-warpper {
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

  .product-tabs {
    .ant-tabs {
      background-color: #FFFFFF;
      padding: 20px;
      padding-top: 10px;
      margin: 16px 19px 0 15px;
    }
  }
}
</style>
