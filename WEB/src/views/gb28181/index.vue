<template>
  <div class="gb28181-container">
    <a-card :bordered="false" class="gb28181-card">
      <a-tabs
        v-model:activeKey="state.activeKey"
        :tab-bar-style="{ margin: 0, padding: '0 24px', background: 'transparent' }"
        size="large"
        type="card"
        @change="handleTabClick"
        class="gb28181-tabs"
      >
        <a-tab-pane key="1">
          <template #tab>
            <span class="tab-label">
              <Icon icon="ant-design:appstore-outlined" class="tab-icon" />
              <span class="tab-text">分屏监控</span>
            </span>
          </template>
          <SplitScreen />
        </a-tab-pane>
        <a-tab-pane key="2">
          <template #tab>
            <span class="tab-label">
              <Icon icon="ant-design:video-camera-outlined" class="tab-icon" />
              <span class="tab-text">国标设备</span>
            </span>
          </template>
          <Video />
        </a-tab-pane>
        <a-tab-pane key="3">
          <template #tab>
            <span class="tab-label">
              <Icon icon="ant-design:cloud-download-outlined" class="tab-icon" />
              <span class="tab-text">拉流代理</span>
            </span>
          </template>
          <PullProxy />
        </a-tab-pane>
        <a-tab-pane key="4">
          <template #tab>
            <span class="tab-label">
              <Icon icon="ant-design:cluster-outlined" class="tab-icon" />
              <span class="tab-text">节点管理</span>
            </span>
          </template>
          <Node />
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<script lang="ts" setup name="GB28181">
import { reactive } from 'vue';
import { Card as ACard, Tabs as ATabs } from 'ant-design-vue';
import { Icon } from '@/components/Icon';
import Video from '@/views/gb28181/components/Video/index.vue';
import SplitScreen from '@/views/gb28181/components/SplitScreen/index.vue';
import PullProxy from '@/views/gb28181/components/PullProxy/index.vue';
import Node from '@/views/gb28181/components/Node/index.vue';

const state = reactive({
  activeKey: '1',
});

const handleTabClick = (activeKey: string) => {
  state.activeKey = activeKey;
};
</script>

<style lang="less" scoped>
.gb28181-container {
  height: 100%;
  background: #ffffff;
  padding: 0;
  position: relative;

  &::before {
    display: none;
  }

  .gb28181-card {
    height: 100%;
    box-shadow: none;
    border-radius: 0;
    overflow: hidden;
    background: #ffffff;
    backdrop-filter: none;
    border: none;

    :deep(.ant-card-body) {
      height: 100%;
      padding: 0;
      display: flex;
      flex-direction: column;
      background: transparent;
    }

    .gb28181-tabs {
      height: 100%;
      display: flex;
      flex-direction: column;

      :deep(.ant-tabs-content-holder) {
        flex: 1;
        overflow: hidden;
      }

      :deep(.ant-tabs-content) {
        height: 100%;
      }

      :deep(.ant-tabs-content-holder .ant-tabs-content .ant-tabs-tabpane.ant-tabs-tabpane-active) {
        height: 100% !important;
        min-height: 100% !important;
        display: block !important;
        
        > * {
          height: 100% !important;
          min-height: 100% !important;
        }
      }
      
      :deep(.ant-tabs-tabpane-active) {
        height: 100% !important;
        min-height: 100% !important;
        display: block !important;
        
        > * {
          height: 100% !important;
          min-height: 100% !important;
        }
      }

      :deep(.ant-tabs-nav) {
        margin: 0;
        padding: 0 24px;
        background: #ffffff;
        border-bottom: 1px solid #e5e7eb;
        position: relative;

        &::after {
          display: none;
        }

        .ant-tabs-tab {
          padding: 16px 24px;
          margin: 0 4px;
          font-size: 14px;
          font-weight: 500;
          color: #6b7280;
          transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
          border-radius: 8px 8px 0 0;
          border: 1px solid transparent;
          border-bottom: none;
          background: transparent;
          position: relative;

          &::before {
            display: none;
          }

          &:hover {
            color: #3b82f6;
            background: rgba(59, 130, 246, 0.08);
            border-color: rgba(59, 130, 246, 0.2);

            .tab-icon {
              transform: scale(1.1);
              color: #3b82f6;
            }
          }

          &.ant-tabs-tab-active {
            background: rgba(59, 130, 246, 0.1);
            border-color: rgba(59, 130, 246, 0.3);
            color: #3b82f6;

            .ant-tabs-tab-btn {
              color: #3b82f6;
              font-weight: 600;
            }

            .tab-icon {
              color: #3b82f6;
              transform: scale(1.1);
            }
          }

          .tab-label {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            position: relative;
            z-index: 1;

            .tab-icon {
              font-size: 16px;
              transition: all 0.3s;
              color: inherit;
            }

            .tab-text {
              font-weight: inherit;
            }
          }
        }

        .ant-tabs-ink-bar {
          background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);
          height: 3px;
          border-radius: 2px;
          box-shadow: 0 0 8px rgba(59, 130, 246, 0.6);
        }

        .ant-tabs-nav-operations {
          .ant-tabs-nav-more {
            color: #6b7280;
            
            &:hover {
              color: #3b82f6;
            }
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .gb28181-container {
    padding: 0;

    .gb28181-card {
      border-radius: 0;

      :deep(.ant-tabs-nav) {
        padding: 0 12px;

        .ant-tabs-tab {
          padding: 12px 16px;
          font-size: 13px;

          .tab-label {
            gap: 6px;

            .tab-icon {
              font-size: 14px;
            }
          }
        }
      }
    }
  }
}
</style>