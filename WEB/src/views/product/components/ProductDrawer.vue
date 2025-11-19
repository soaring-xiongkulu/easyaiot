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
          <PhysicalModal
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
import PhysicalModal from './PhysicalModal.vue';
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
  overflow-y: auto;
  background: #f5f7fa;
  padding: 24px;
  height: 100%;

  .detail-info {
    margin-bottom: 24px;
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
    background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
    border-radius: 12px;
    margin: 0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(0, 0, 0, 0.06);
    transition: all 0.3s ease;

    &:hover {
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
    }

    .ant-card-body {
      padding: 28px;

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

        .ant-btn {
          line-height: 1.5715;
          position: relative;
          display: inline-block;
          font-weight: 500;
          white-space: nowrap;
          text-align: center;
          background-image: none;
          border: 1px solid transparent;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          -webkit-user-select: none;
          -moz-user-select: none;
          user-select: none;
          touch-action: manipulation;
          height: 36px;
          padding: 4px 20px;
          font-size: 14px;
          border-radius: 8px;
          color: #000000d9;
          border-color: #d9d9d9;
          background: #fff;

          &:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12);
          }
        }

        .ant-btn-primary {
          color: #fff;
          background: #1890ff;
          border-color: #1890ff;

          &:hover {
            background: #40a9ff;
            border-color: #40a9ff;
          }
        }

        .ant-btn-dangerous.ant-btn-primary {
          border-color: #ff4d4f;
          background: #ff4d4f;
          text-shadow: 0 -1px 0 rgba(0, 0, 0, 0.12);
          box-shadow: 0 2px 4px rgba(255, 77, 79, 0.3);

          &:hover {
            background: #ff7875;
            border-color: #ff7875;
          }
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
  }

  .product-tabs {
    margin: 0;
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    border: 1px solid rgba(0, 0, 0, 0.06);
    overflow: hidden;

    .ant-tabs {
      background-color: #ffffff;
      padding: 20px 24px;
      padding-top: 16px;
      margin: 0;
    }

    :deep(.ant-tabs-nav) {
      margin-bottom: 24px;
      padding: 0;
    }

    :deep(.ant-tabs-content-holder) {
      padding: 0 24px 24px;
    }

    :deep(.ant-tabs-tab) {
      padding: 12px 24px;
      font-size: 15px;
      font-weight: 500;
      color: #666;
      transition: all 0.3s ease;
      margin-right: 8px;

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
