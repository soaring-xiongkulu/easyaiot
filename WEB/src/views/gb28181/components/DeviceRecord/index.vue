<template>
  <div id="devicePosition" style="width: 100vw; height: 93vh;">
    <section class="el-container">
      <aside class="el-aside" style="width: 300px;">
        <div class="record-list-box-box">
          <div
            class="el-date-editor el-input el-input--mini el-input--prefix el-input--suffix el-date-editor--date"
            style="margin: 10px auto;">
            <DatePicker
              v-model:value="state.dateValue"
              allowClear
              valueFormat="YYYY-MM-DD"
              style="width: 100%"
              @change="dateChange"
            />
          </div>
          <div class="record-list-box" style="overflow: auto; margin: 10px auto; height: 820px;">
            <Button type="primary" style="left: 41px;width: 138px;"
                    :onclick="queryDeviceRecords.bind(null)">刷新列表
            </Button>
            <ul class="infinite-list record-list" v-for="(item, index) of state.recordList">
              <li class="infinite-list-item record-list-item">
                <span class="el-tag el-tag--light" :onclick="handleRecordPlay.bind(null, item)">
                  <Icon icon="bx:video-recording"/>
                  {{ item['startTime'].substr(10) }}-{{ item['endTime'].substr(10) }}
                </span>
<!--                <Icon icon="mingcute:download-2-line" :onclick="handleRecordDownload.bind(null, item)" style="color: #409EFF;margin-left: 10px"/>-->
              </li>
            </ul>
          </div>
        </div>
      </aside>
      <main class="el-main" style="padding-bottom: 10px;height: 100%">
        <div class="playBox" style="margin: 12px auto 20px;height: 818px;">
          <Jessibuca ref="jessibuca" :play-url="state.playUrl" :hasAudio="false"
                     style="width: 94%; "/>
        </div>
        <!--        <div class="player-option-box">-->
        <!--          <Slider v-model:value="sliderSpan" :max="24"/>-->
        <!--        </div>-->
      </main>
    </section>
  </div>
</template>
<script lang="ts" setup>
import {onBeforeUnmount, onMounted, reactive} from 'vue'
import {Button, DatePicker} from 'ant-design-vue';
import {useMessage} from "@/hooks/web/useMessage";
import {getDeviceRecordList, playBack} from "@/api/device/gb28181";
import {useRoute} from "vue-router";
import moment from 'moment'
import {Icon} from "@/components/Icon";
import Jessibuca from "@/components/Player/module/jessibuca.vue";

const {createMessage} = useMessage()
const route = useRoute()

const state = reactive({
  playUrl: '',
  dateValue: moment(new Date()).format('YYYY-MM-DD'),
  recordList: [],
});

const dateChange = (e: any) => {
  state.dateValue = e;
  queryDeviceRecords();
};

const queryDeviceRecords = () => {
  getDeviceRecordList(route.params.deviceId, route.params.channelId, state.dateValue + " 00:00:00", state.dateValue + " 23:59:59").then((res) => {
    state.recordList = res['data']['recordList'];
  });
};

function initDeviceRecordList() {
  queryDeviceRecords();
}

function handleRecordPlay(params) {
  //deviceId, channelId, startTime, endTime
  playBack(route.params.deviceId, route.params.channelId, params['startTime'], params['endTime']).then((res) => {
    state.playUrl = res['ws_flv'];
  })
}

onMounted(() => {
  initDeviceRecordList();
})
</script>

<style>
#devicePosition {
  .el-container {
    display: -webkit-box;
    display: -ms-flexbox;
    display: flex;
    -webkit-box-orient: horizontal;
    -webkit-box-direction: normal;
    -ms-flex-direction: row;
    flex-direction: row;
    -webkit-box-flex: 1;
    -ms-flex: 1;
    flex: 1;
    -ms-flex-preferred-size: auto;
    flex-basis: auto;
    -webkit-box-sizing: border-box;
    box-sizing: border-box;
    min-width: 0;
    height: 100%;

    .el-aside {
      overflow: auto;
      -webkit-box-sizing: border-box;
      box-sizing: border-box;
      -ms-flex-negative: 0;
      flex-shrink: 0;

      .record-list-box-box {
        width: 250px;
        float: left;

        .record-list-box {
          overflow: auto;
          width: 220px;
          list-style: none;
          padding: 0;
          margin: 0;
          margin-top: 0px;
          padding: 1rem 0;
          background-color: #FFF;
          margin-top: 10px;

          .record-list {
            list-style: none;
            padding: 0;
            margin: 0;
            background-color: #FFF;

            .record-list-item {
              padding: 0;
              margin: 0;
              margin: 0.5rem 0;
              cursor: pointer;
              text-align: center;

              .el-tag {
                background-color: #ecf5ff;
                border-color: #d9ecff;
                height: 32px;
                padding: 0 10px;
                line-height: 30px;
                font-size: 0.75rem;
                color: #409EFF;
                border-width: 1px;
                border-style: solid;
                border-radius: 4px;
                -webkit-box-sizing: border-box;
                box-sizing: border-box;
                white-space: nowrap;
                display: inline-block;
              }
            }
          }
        }

        .el-date-editor.el-input, .el-date-editor.el-input__inner {
          width: 220px;
        }

        .el-input--mini {
          font-size: 0.75rem;

          .el-input__inner {
            height: 28px;
            line-height: 28px;
          }

          .el-input__inner {
            -webkit-appearance: none;
            background-color: #FFF;
            background-image: none;
            border-radius: 4px;
            border: 1px solid #DCDFE6;
            -webkit-box-sizing: border-box;
            box-sizing: border-box;
            color: #606266;
            display: inline-block;
            height: 40px;
            line-height: 40px;
            outline: 0;
            padding: 0 15px;
            -webkit-transition: border-color .2s cubic-bezier(.645, .045, .355, 1);
            transition: border-color .2s cubic-bezier(.645, .045, .355, 1);
            width: 100%;
          }

          .el-input__prefix {
            height: 100%;
            left: 5px;
            -webkit-transition: all .3s;
            transition: all .3s;

            .el-input__icon {
              line-height: 28px;
            }

            .el-input__icon {
              height: 100%;
              width: 25px;
              text-align: center;
              -webkit-transition: all .3s;
              transition: all .3s;
              line-height: 40px;
            }
          }

          .el-input__suffix {
            height: 100%;
            right: 5px;
            -webkit-transition: all .3s;
            transition: all .3s;
            pointer-events: none;

            .el-input__suffix-inner {
              pointer-events: all;

              .el-input__icon {
                height: 100%;
                width: 25px;
                text-align: center;
                -webkit-transition: all .3s;
                transition: all .3s;
                line-height: 40px;
              }

              .el-input--mini .el-input__icon {
                line-height: 28px;
              }
            }
          }
        }

        .el-input {
          position: relative;
          font-size: 0.875rem;
        }
      }
    }

    .el-main {
      color: #333;
      text-align: center;
      padding-top: 0px !important;
      display: block;
      -webkit-box-flex: 1;
      -ms-flex: 1;
      flex: 1;
      -ms-flex-preferred-size: auto;
      flex-basis: auto;
      overflow: auto;
      -webkit-box-sizing: border-box;
      box-sizing: border-box;

      .player-option-box {

        .el-button-group {
          display: inline-block;
          vertical-align: middle;

          .el-range-editor--mini.el-input__inner {
            height: 28px;
          }

          .el-range-editor.el-input__inner {
            display: -webkit-inline-box;
            display: -ms-inline-flexbox;
            display: inline-flex;
            -webkit-box-align: center;
            -ms-flex-align: center;
            align-items: center;
            padding: 3px 10px;

            .el-input__icon {
              height: 100%;
              width: 25px;
              text-align: center;
              -webkit-transition: all .3s;
              transition: all .3s;
              line-height: 40px;
            }

            .el-date-editor .el-range__icon {
              font-size: 0.875rem;
              margin-left: -5px;
              color: #C0C4CC;
              float: left;
              line-height: 32px;
            }
          }
        }

        .playtime-slider {
          position: relative;
          z-index: 100;
        }

        .slider-val-box {
          height: 6px;
          position: relative;
          top: -22px;
        }
      }
    }
  }
}
</style>
