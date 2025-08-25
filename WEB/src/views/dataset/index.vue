<template>
  <div class="device-wrapper">
    <div class="device-tab">
      <Tabs
        :animated="{ inkBar: true, tabPane: true }"
        :activeKey="state.activeKey"
        :tabBarGutter="60"
        @tabClick="handleTabClick"
      >
        <DatasetList></DatasetList>
      </Tabs>
    </div>
  </div>
</template>
<script lang="ts" setup name="noticeSetting">
import {reactive} from 'vue';
import {Tabs} from "ant-design-vue";
import DatasetList from "@/views/dataset/components/DatasetList/index.vue";

defineOptions({name: 'DATASET'})

const state = reactive({
  isTableMode: true,
  activeKey: '1',
  pushActiveKey: '1',
  historyActiveKey: '1',
  SmsActiveKey: '1',
});

const handleTabClick = (activeKey) => {
  state.activeKey = activeKey;
};
</script>

<style lang="less" scoped>
:deep(.iot-basic-table-action.left) {
  justify-content: center;
}

.device-wrapper {
  :deep(.ant-tabs-nav) {
    padding: 5px 0 0 25px;
  }

  :deep(.ant-form-item) {
    margin-bottom: 10px;
  }

  .device-tab {
    padding: 16px 19px 0 15px;

    .ant-tabs {
      background-color: #FFFFFF;

      :deep(.ant-tabs-nav) {
        padding: 5px 0 0 25px;
      }
    }
  }

  .device-info {
    padding: 16px 16px 0;

    .ant-row {
      display: flex;
      flex-flow: row wrap;

      .ant-col {
        margin-top: 6px !important;
        margin-bottom: 6px !important;
        position: relative;
        min-height: 1px;

        .ant-card {
          box-sizing: border-box;
          margin: 0;
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
          box-shadow: 0 0 4px #00000026;

          .ant-card-body {
            padding: 24px;

            .card-box {
              display: flex;

              .img {
                width: 104px;
                margin-right: 8px;
                border-radius: 10px;
              }

              .info-box {
                flex: 1;

                .title {
                  font-size: 12px;
                  line-height: 1;
                  font-weight: 600;
                  margin-bottom: 10px;
                  padding-left: 8px;
                }

                .list {
                  display: flex;

                  .item {
                    flex: 1;
                    text-align: center;

                    .num {
                      font-size: 26px;
                      font-weight: 600;
                    }

                    .name {
                      font-weight: 600;
                    }
                  }
                }
              }
            }
          }

          .ant-card-body:before {
            display: table;
            content: "";
          }

          .ant-card-body:after {
            display: table;
            clear: both;
            content: "";
          }
        }
      }
    }

    .ant-col-7 {
      display: block;
      flex: 0 0 29.1%;
      max-width: 29.1%;
    }

    .ant-col-10 {
      display: block;
      flex: 0 0 41.6%;
      max-width: 41.6%;
    }
  }

  .device-tab {
    padding: 16px 19px 0 15px;

    .ant-tabs {
      background-color: #FFFFFF;
    }
  }
}
</style>
