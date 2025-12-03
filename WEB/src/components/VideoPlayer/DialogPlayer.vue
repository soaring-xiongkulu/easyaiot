<template>
  <BasicModal
    @register="register"
    title="视频播放"
    :footer=null
    :width="900"
    :canFullscreen="true"
    :zIndex="10000"
    @cancel="handleCancel"
  >
    <div class="ant-modal-content">
      <div class="ant-modal-body" style="padding: 0px;">
        <div style="min-height: 200px; max-height: 680px;">
          <!-- 播放器 -->
          <div style="height: 420px">
            <Jessibuca ref="jessibuca" :playUrl="state.currentUrl" :hasAudio="false"/>
          </div>
          <!-- 控制台 -->
          <div class="tabs">
            <Tabs v-model:activeKey="state.activeKey">
              <TabPane key="info" tab="实时视频">
                <div class="real-time-info">
                  <div>
                    <div class="label" style="margin: 0 0 8px 0;">播放地址：</div>
                    <span class="ant-input-group-wrapper"><span
                      class="ant-input-wrapper ant-input-group">
                      <input type="text"
                             :disabled="true"
                             class="ant-input ant-input-disabled" :value="state.currentUrl"><span
                      class="ant-input-group-addon">
                     <svg style="cursor: pointer;"
                          :onclick="handleCopy.bind(null, state.currentUrl)"
                          xmlns="http://www.w3.org/2000/svg" width="22" height="22"
                          viewBox="0 0 1024 1024"><path fill="currentColor"
                                                        d="M856 376H648V168c0-8.8-7.2-16-16-16H168c-8.8 0-16 7.2-16 16v464c0 8.8 7.2 16 16 16h208v208c0 8.8 7.2 16 16 16h464c8.8 0 16-7.2 16-16V392c0-8.8-7.2-16-16-16m-480 16v188H220V220h360v156H392c-8.8 0-16 7.2-16 16m204 52v136H444V444zm224 360H444V648h188c8.8 0 16-7.2 16-16V444h156z"/></svg>
                    </span></span></span>
                  </div>
                  <div>
                    <div class="label">iframe：</div>
                    <span class="ant-input-group-wrapper">
                      <span class="ant-input-wrapper ant-input-group">
                      <input type="text"
                             :disabled="true"
                             class="ant-input ant-input-disabled" :value="state.iframeUrl"><span
                        class="ant-input-group-addon">
                        <svg style="cursor: pointer;"
                             :onclick="handleCopy.bind(null, state.iframeUrl)"
                             xmlns="http://www.w3.org/2000/svg" width="22" height="22"
                             viewBox="0 0 1024 1024"><path fill="currentColor"
                                                           d="M856 376H648V168c0-8.8-7.2-16-16-16H168c-8.8 0-16 7.2-16 16v464c0 8.8 7.2 16 16 16h208v208c0 8.8 7.2 16 16 16h464c8.8 0 16-7.2 16-16V392c0-8.8-7.2-16-16-16m-480 16v188H220V220h360v156H392c-8.8 0-16 7.2-16 16m204 52v136H444V444zm224 360H444V648h188c8.8 0 16-7.2 16-16V444h156z"/></svg>
                      </span>
                      </span>
                    </span>
                  </div>
                  <div>
                    <div class="label">资源地址：</div>
                    <span class="ant-input-group-wrapper">
                      <Select
                        v-model:value="state.mediaType"
                        :options="state.videoUrlList"
                        @change="handleChange"
                        style="width: 150px;"
                      />
                      <span class="ant-input-wrapper ant-input-group">
                      <input type="text"
                             :disabled="true"
                             class="ant-input ant-input-disabled" :value="state.currentUrl"><span
                        class="ant-input-group-addon">
                        <svg style="cursor: pointer;"
                             :onclick="handleCopy.bind(null, state.currentUrl)"
                             xmlns="http://www.w3.org/2000/svg" width="22" height="22"
                             viewBox="0 0 1024 1024"><path fill="currentColor"
                                                           d="M856 376H648V168c0-8.8-7.2-16-16-16H168c-8.8 0-16 7.2-16 16v464c0 8.8 7.2 16 16 16h208v208c0 8.8 7.2 16 16 16h464c8.8 0 16-7.2 16-16V392c0-8.8-7.2-16-16-16m-480 16v188H220V220h360v156H392c-8.8 0-16 7.2-16 16m204 52v136H444V444zm224 360H444V648h188c8.8 0 16-7.2 16-16V444h156z"/></svg>
                      </span>
                      </span>
                    </span>
                  </div>
                </div>
                <section class="full-loading absolute" style="display: none;">
                  <div class="ant-spin ant-spin-lg"><span
                    class="ant-spin-dot ant-spin-dot-spin"><i class="ant-spin-dot-item"></i><i
                    class="ant-spin-dot-item"></i><i class="ant-spin-dot-item"></i><i
                    class="ant-spin-dot-item"></i></span></div>
                </section>
              </TabPane>
              <TabPane key="camera" tab="云台控制">
                <Ptz @ptz-camera="handlePtzCamera" style="width: 100%"/>
              </TabPane>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import {useModalInner} from "@/components/Modal";
import BasicModal from "@/components/Modal/src/BasicModal.vue";

import {reactive, ref} from "vue";
import {Select, TabPane, Tabs} from 'ant-design-vue';
import Jessibuca from "@/components/Player/module/jessibuca.vue";
import Ptz from "@/components/Player/module/ptz.vue";
import {copyText} from "@/utils/copyTextToClipboard";
import {useMessage} from "@/hooks/web/useMessage";
import {controlPTZ} from "@/api/device/camera";

const {createMessage} = useMessage()

let jessibuca = ref()
//state.videoUrl
const state = reactive({
  video: 'http://lndxyj.iqilu.com/public/upload/2019/10/14/8c001ea0c09cdc59a57829dabc8010fa.mp4',
  videoUrl: '',
  activePlayer: "jessibuca",
  presetPos: '',
  deviceIdentification: '',
  // 如何你只是用一种播放器，直接注释掉不用的部分即可
  player: {
    jessibuca: ["ws_flv", "flv"],
    webRTC: ["rtc", "rtcs"],
  },
  hasAudio: false,
  currentUrl: '',
  iframeUrl: '',
  mediaType: 'flv',
  videoUrlList: [{label: 'flv', value: "1"}],
  deviceId: '',
  activeKey: 'info',
  playerOptions: {
    aspectRatio: '16:5',
    controls: true,
    loop: true,
    volume: 0.6,
    notSupportedMessage: '此视频暂无法播放，请稍后再试',
  },
})

const [register, {closeModal}] = useModalInner((record) => {
  state.deviceId = record['id'];
  state.currentUrl = record['http_stream'];
  state.iframeUrl = "<iframe src=\"" + record['http_stream'] + "\"></iframe>"
  state.videoUrlList = [
    {label: 'http_stream', value: record['http_stream']}
  ];
});

const handleChange = (value: string) => {
  copyText(value);
};

const handleCopy = (value: string) => {
  copyText(value);
};

const handlePtzCamera = (command: string, speed: number) => {
  // 方向指令映射为坐标
  const directionMap = {
    UP:    { x: 0, y: speed, z: 0 },
    DOWN:  { x: 0, y: -speed, z: 0 },
    LEFT:  { x: -speed, y: 0, z: 0 },
    RIGHT: { x: speed, y: 0, z: 0 },
    ZOOM_IN:  { x: 0, y: 0, z: speed },
    ZOOM_OUT: { x: 0, y: 0, z: -speed }
  };
  // 停止指令（松开按钮时发送）
  if (command === 'STOP') {
    controlPTZ(state.deviceId, { x: 0, y: 0, z: 0 });
  } else if (directionMap[command]) {
    controlPTZ(state.deviceId, directionMap[command]);
  }
}

function handleCancel() {
  state.currentUrl = '';
  closeModal();
}
</script>

<style>
.ant-modal-content {

  .ant-modal-body {
    padding: 0px;

    & > .scrollbar {
      position: relative;
      height: 100%;
      overflow: hidden;
      padding: 0;
    }

    .scroll-container {
      width: 100%;
      height: 100%;

      .scrollbar__wrap--hidden-default {
        scrollbar-width: none;
      }

      .scrollbar__wrap {
        margin-bottom: 18px !important;
        overflow-x: hidden;

        .scroll-container .scrollbar__view {
          box-sizing: border-box;
        }

        .root {
          display: flex;

          .container-shell {
            width: 100%;
            position: relative;
            background: #000;
            padding: 30px 0 0;
            border-radius: 4px;

            .performance {
              position: absolute;
              top: 10px;
              right: 14px;
              display: flex;
              align-items: center;
              gap: 12px;

              .k-bps {
                color: #fff;
                font-size: 12px;
              }

              .performance-content {
                width: 12px;
                height: 12px;
                border-radius: 50%;
              }
            }

            .vide-main {
              position: relative;

              #container {
                background: rgba(13, 14, 27, .7);
                height: 350px;
              }

              .jessibuca-container {
                position: relative;
                display: block;
                width: 100%;
                height: 100%;
                overflow: hidden;

                .jessibuca-loading {
                  display: none;
                  flex-direction: column;
                  justify-content: center;
                  align-items: center;
                  position: absolute;
                  z-index: 20;
                  left: 0;
                  top: 0;
                  right: 0;
                  bottom: 0;
                  width: 100%;
                  height: 100%;
                  pointer-events: none;

                  .icon-title-tips {
                    pointer-events: none;
                    position: absolute;
                    left: 50%;
                    bottom: 100%;
                    visibility: hidden;
                    opacity: 0;
                    transform: translateX(-50%);
                    transition: visibility .3s ease 0s, opacity .3s ease 0s;
                    background-color: rgba(0, 0, 0, .5);
                    border-radius: 4px;

                    .icon-title {
                      display: inline-block;
                      padding: 5px 10px;
                      font-size: 12px;
                      white-space: nowrap;
                      color: #fff;
                    }
                  }

                  .jessibuca-icon-loading {
                    width: 50px;
                    height: 50px;
                    background: url(data:image/png;base64,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) no-repeat 50%;
                    background-size: 100% 100%;
                    animation: rotation 1s linear infinite;
                  }

                  .jessibuca-loading-text {
                    line-height: 20px;
                    font-size: 13px;
                    color: #fff;
                    margin-top: 10px;
                  }
                }
              }
            }

            .bottom-operate {
              background-color: #ffffff80;
              display: flex;
              align-items: center;
              justify-content: space-between;
              padding: 0 8px;

              .operate-left {
                .operate-icon {
                  transition: all linear .2s;
                  cursor: pointer;
                }

                .thinglinks-svg-icon {
                  display: inline-block;
                  overflow: hidden;
                  vertical-align: -.15em;
                  fill: currentColor;
                }
              }

              .operate-right {
                display: flex;
                align-items: center;
                gap: 10px;

                .volume-control {
                  display: flex;
                  align-items: center;

                  .operate-icon {
                    transition: all linear .2s;
                    cursor: pointer;
                  }

                  .thinglinks-svg-icon {
                    display: inline-block;
                    overflow: hidden;
                    vertical-align: -.15em;
                    fill: currentColor;
                  }

                  .slider-wrapper {
                    width: 100px;
                  }

                  .ant-slider {
                    box-sizing: border-box;
                    color: #000000d9;
                    font-size: 14px;
                    font-variant: tabular-nums;
                    line-height: 1.5715;
                    list-style: none;
                    font-feature-settings: "tnum";
                    position: relative;
                    height: 12px;
                    margin: 10px 6px;
                    padding: 4px 0;
                    cursor: pointer;
                    touch-action: none;

                    .ant-slider-rail {
                      position: absolute;
                      width: 100%;
                      height: 4px;
                      background-color: #f5f5f5;
                      border-radius: 2px;
                      transition: background-color .3s;
                    }

                    .ant-slider-track {
                      position: absolute;
                      height: 4px;
                      background-color: #5bbda9;
                      border-radius: 2px;
                      transition: background-color .3s;
                    }

                    .ant-slider-step {
                      position: absolute;
                      width: 100%;
                      height: 4px;
                      background: transparent;
                    }

                    .ant-slider-handle {
                      position: absolute;
                      width: 14px;
                      height: 14px;
                      margin-top: -5px;
                      background-color: #fff;
                      border-radius: 50%;
                      box-shadow: 0;
                      cursor: pointer;
                      border: solid 2px #5bbda9;
                      transition: border-color .3s, box-shadow .6s, transform .3s cubic-bezier(.18, .89, .32, 1.28);
                    }

                    .ant-slider-mark {
                      position: absolute;
                      top: 14px;
                      left: 0;
                      width: 100%;
                      font-size: 14px;
                    }
                  }
                }

                .operate-icon {
                  transition: all linear .2s;
                  cursor: pointer;
                }

                .thinglinks-svg-icon {
                  display: inline-block;
                  overflow: hidden;
                  vertical-align: -.15em;
                  fill: currentColor;
                }
              }
            }
          }
        }

        .real-time-info {
          .label {
            margin: 8px 0;
          }

          .ant-input-group-wrapper {
            display: flex;
            width: 100%;
            text-align: start;
            vertical-align: top;

            .ant-input-group {
              box-sizing: border-box;
              margin: 0;
              padding: 0;
              color: #000000d9;
              font-size: 14px;
              font-variant: tabular-nums;
              line-height: 1.5715;
              list-style: none;
              font-feature-settings: "tnum";
              position: relative;
              display: table;
              width: 100%;
              border-collapse: separate;
              border-spacing: 0;

              .ant-input {
                float: left;
                width: 100%;
                margin-bottom: 0;
                text-align: inherit;
                box-sizing: border-box;
                margin: 0;
                font-variant: tabular-nums;
                list-style: none;
                font-feature-settings: "tnum";
                position: relative;
                display: inline-block;
                width: 100%;
                min-width: 0;
                padding: 4px 11px;
                color: #000000d9;
                font-size: 14px;
                line-height: 1.5715;
                background-color: #fff;
                background-image: none;
                border: 1px solid #d9d9d9;
                border-top-width: 1px;
                border-right-width: 1px;
                border-bottom-width: 1px;
                border-left-width: 1px;
                border-top-style: solid;
                border-right-style: solid;
                border-bottom-style: solid;
                border-left-style: solid;
                border-top-color: rgb(217, 217, 217);
                border-right-color: rgb(217, 217, 217);
                border-bottom-color: rgb(217, 217, 217);
                border-left-color: rgb(217, 217, 217);
                border-image-source: initial;
                border-image-slice: initial;
                border-image-width: initial;
                border-image-outset: initial;
                border-image-repeat: initial;
                border-radius: 2px;
                border-top-left-radius: 2px;
                border-top-right-radius: 2px;
                border-bottom-right-radius: 2px;
                border-bottom-left-radius: 2px;
                transition: all .3s;
              }

              .ant-input[disabled] {
                color: #00000040;
                background-color: #f5f5f5;
                border-color: #d9d9d9;
                box-shadow: none;
                cursor: not-allowed;
                opacity: 1;
              }

              & > .ant-input:last-child, .ant-input-group-addon:last-child {
                border-top-left-radius: 0;
                border-bottom-left-radius: 0;
              }

              .ant-input-group-addon:last-child {
                border-left: 0;
              }

              .ant-input-group-addon, .ant-input-group-wrap {
                width: 1px;
                white-space: nowrap;
                vertical-align: middle;
              }

              .ant-input-group-addon, .ant-input-group-wrap, .ant-input-group > .ant-input {
                display: table-cell;
              }

              .ant-input-group-addon {
                position: relative;
                padding: 0 11px;
                color: #000000d9;
                font-weight: 400;
                font-size: 14px;
                text-align: center;
                background-color: #fafafa;
                border: 1px solid #d9d9d9;
                border-radius: 2px;
                transition: all .3s;

                .ant-select {
                  box-sizing: border-box;
                  margin: 0;
                  padding: 0;
                  color: #000000d9;
                  font-size: 14px;
                  font-variant: tabular-nums;
                  line-height: 1.5715;
                  list-style: none;
                  font-feature-settings: "tnum";
                  position: relative;
                  display: inline-block;
                  cursor: pointer;

                  &.ant-select-single:not(.ant-select-customize-input) .ant-select-selector {
                    background-color: inherit;
                    border: 1px solid transparent;
                    border-top-width: 1px;
                    border-right-width: 1px;
                    border-bottom-width: 1px;
                    border-left-width: 1px;
                    border-top-style: solid;
                    border-right-style: solid;
                    border-bottom-style: solid;
                    border-left-style: solid;
                    border-top-color: transparent;
                    border-right-color: transparent;
                    border-bottom-color: transparent;
                    border-left-color: transparent;
                    border-image-source: initial;
                    border-image-slice: initial;
                    border-image-width: initial;
                    border-image-outset: initial;
                    border-image-repeat: initial;
                    box-shadow: none;
                  }

                  &:not(.ant-select-customize-input) .ant-select-selector .ant-select-selection-search-input {
                    margin: 0;
                    padding: 0;
                    background: transparent;
                    border: none;
                    border-top-width: initial;
                    border-right-width: initial;
                    border-bottom-width: initial;
                    border-left-width: initial;
                    border-top-style: none;
                    border-right-style: none;
                    border-bottom-style: none;
                    border-left-style: none;
                    border-top-color: initial;
                    border-right-color: initial;
                    border-bottom-color: initial;
                    border-left-color: initial;
                    border-image-source: initial;
                    border-image-slice: initial;
                    border-image-width: initial;
                    border-image-outset: initial;
                    border-image-repeat: initial;
                    outline: none;
                    -webkit-appearance: none;
                    -moz-appearance: none;
                    appearance: none;
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
</style>
