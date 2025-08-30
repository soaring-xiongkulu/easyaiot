<template>
  <a-modal
    ref="playerRef"
    v-model:visible="open"
    :title="title"
    width="67vw"
    :wrap-style="{ overflow: 'hidden' }"
    @cancel="closeModel"
    :footer="null"
  >
    <a-row>
      <a-col style="width: 54vw">
        <div style="width: 100%; height: 32vw">
          <a-radio-group
            v-model:value="playerType"
            @change="playerTypeChange"
            style="width: 100%; height: 1.625vw; padding: 0 2px; min-height: 34px"
          >
            <a-radio-button value="1">Jessibuca</a-radio-button>
            <a-radio-button value="2">WebRTC</a-radio-button>
            <a-radio-button value="3">Video标签</a-radio-button>
          </a-radio-group>
          <div v-if="playerType == 1" style="width: 100%; height: 30.375vw">
            <Jessibuca ref="jessibuca" :play-url="playUrl" :hasAudio="false" />
          </div>
          <div v-if="playerType == 2" style="width: 100%; height: 30.375vw">
            <RtcPlayer ref="rtcPlayer" :play-url="playUrl" :hasAudio="false" />
          </div>
          <div v-if="playerType == 3" style="width: 100%; height: 30.375vw">
            <video controls autoplay style="width: 100%; height: 30.375vw">
              <source :src="playUrl" type="video/mp4" />
            </video>
          </div>
        </div>
      </a-col>
      <a-col style="width: 13vw; height: 32vw; overflow: auto">
        <a-tabs style="width: 100%" size="small" type="card">
          <a-tab-pane key="1" tab="控制" v-if="!hideControlTab">
            <Ptz @ptz-camera="ptzCamera" style="width: 100%" />
          </a-tab-pane>
          <a-tab-pane key="2" tab="设置" v-if="!hideControlTab">
            <div style="height: 32vw; padding: 0 1rem">
              <a-select ref="select" v-model:value="ptzControlType" class="ptz-space">
                <a-select-option value="1">预置位</a-select-option>
                <a-select-option value="2">巡航组</a-select-option>
                <a-select-option value="3">水平扫描</a-select-option>
                <a-select-option value="4">雨刷</a-select-option>
                <a-select-option value="5">辅助开关</a-select-option>
                <a-select-option value="6">强制关键帧</a-select-option>
                <a-select-option value="7">看守位控制</a-select-option>
              </a-select>
              <div v-if="ptzControlType==1">
                <a-input-number
                  min="1"
                  max="255"
                  v-model:value="ptzPresetId"
                  placeholder="预置位编号"
                  addonBefore="预置位编号"
                  addonAfter="(1-255)"
                  class="ptz-space"
                />
                <a-button-group>
                  <a-button @click="gotoPreset()" title="移动镜头到预置位">查看</a-button>
                  <a-button @click="setPreset()" title="设置当前镜头为此预置位">添加</a-button>
                  <a-button @click="delPreset()" title="删除此预置位">删除</a-button>
                </a-button-group>
              </div>
              <div v-if="ptzControlType == 2">
                <a-input-number
                  v-model:value="ptzCruiseId"
                  min="1"
                  max="255"
                  addonBefore="巡航组编号"
                  addonAfter="(1-255)"
                  placeholder="巡航组编号"
                  class="ptz-space"
                />
                <a-button-group class="ptz-space">
                  <a-button @click="startCruise()" title="开始巡航">开始</a-button>
                  <a-button @click="addCruise()" title="添加预置位">添加</a-button>
                  <a-button @click="delCruise()" title="删除巡航组">删除</a-button>
                </a-button-group>
                <a-button-group class="ptz-space">
                  <a-button @click="setCruiseSpeed()" title="设置巡航速度">设置巡航速度</a-button>
                  <a-button @click="setCruiseStay()" title="设置巡航停留时间">
                    设置巡航停留时间
                  </a-button>
                </a-button-group>
                <div v-if="addCruiseSwitch">
                  <a-input-number
                    size="small"
                    min="1"
                    max="255"
                    placeholder="预置位编号"
                    addonBefore="预置位编号"
                    addonAfter="(1-255)"
                    v-model:value="ptzPresetIdForCruise"
                    style="width: 100% !important; margin: 1rem 10px 1rem 0"
                  />
                  <a-button-group size="small">
                    <a-button @click="addPresetForCruise()" title="添加预置位">添加预置位</a-button>
                    <a-button @click="delPresetForCruise()" title="删除预置位">删除预置位</a-button>
                  </a-button-group>
                </div>
                <div v-if="setCruiseSpeedSwitch">
                  <a-input-number
                    size="small"
                    min="1"
                    max="4095"
                    placeholder="巡航速度"
                    addonBefore="巡航速度"
                    addonAfter="(1-4095)"
                    class="ptz-space"
                    v-model:value="ptzCruiseSpeed"
                  />
                  <a-button @click="setCruiseSpeedForSave()" title="设置巡航速度">保存</a-button>
                </div>
                <div v-if="setCruiseStaySwitch">
                  <a-input-number
                    size="small"
                    min="1"
                    max="4095"
                    placeholder="巡航停留时间"
                    addonBefore="巡航停留时间"
                    addonAfter="(1-4095)秒"
                    v-model:value="ptzCruiseStay"
                    class="ptz-space"
                  />
                  <a-button-group size="small">
                    <a-button @click="setCruiseStayForSave()" title="设置巡航停留时间">
                      保存
                    </a-button>
                  </a-button-group>
                </div>
              </div>
              <div v-if="ptzControlType == 3">
                <a-input-number
                  size="small"
                  min="1"
                  max="255"
                  placeholder="扫描组编号"
                  addonBefore="扫描组编号"
                  addonAfter="(1-255)"
                  v-model:value="ptzScanId"
                  class="ptz-space"
                />
                <a-button-group class="ptz-space">
                  <a-button @click="startScan()" title="开始扫描">开始</a-button>
                  <a-button @click="setScan()" title="设置扫描">设置</a-button>
                  <a-button @click="setScanAutoSpeed()" title="设置自动扫描速度">
                    设置自动扫描速度
                  </a-button>
                </a-button-group>
                <a-button-group size="small" v-if="setScanSwitch">
                  <a-button @click="setScanLeft()" title="设置左边界">左边界</a-button>
                  <a-button @click="setScanRight()" title="设置右边界">右边界</a-button>
                </a-button-group>
                <div v-if="setScanAutoSpeedSwitch">
                  <a-input-number
                    size="small"
                    v-model:value="scanAutoSpeed"
                    placeholder="自动扫描速度"
                    addonBefore="自动扫描速度"
                    class="ptz-space"
                  />
                  <a-button
                    size="small"
                    @click="setScanAutoSpeedSwitchSave()"
                    title="设置自动扫描速度"
                  >
                    保存
                  </a-button>
                </div>
              </div>
              <div v-if="ptzControlType == 4">
                <a-button-group class="ptz-space">
                  <a-button @click="startWiper()" title="开启雨刷">开启雨刷</a-button>
                  <a-button @click="stopWiper()" title="关闭雨刷">关闭雨刷</a-button>
                </a-button-group>
              </div>
              <div v-if="ptzControlType == 5">
                <a-input-number
                  min="2"
                  max="255"
                  placeholder="预置位编号"
                  addonBefore="预置位编号"
                  addonAfter="2-255"
                  v-model:value="ptzAuxiliarySwitchId"
                  class="ptz-space"
                />
                <a-button-group>
                  <a-button @click="startAuxiliarySwitch()" title="开启辅助开关">开启</a-button>
                  <a-button @click="stopAuxiliarySwitch()" title="关闭辅助开关">关闭</a-button>
                </a-button-group>
              </div>
              <div v-if="ptzControlType == 6">
                <a-button @click="startForceKeyframe()" title="发送强制关键帧">发送</a-button>
              </div>
              <div v-if="ptzControlType == 7">
                <a-input-number
                  size="small"
                  min="1"
                  max="255"
                  placeholder="预置位编号"
                  addonBefore="预置位编号"
                  addonAfter="(1-255)"
                  v-model:value="ptzPresetIdForHomePosition"
                  class="ptz-space"
                />
                <a-input-number
                  size="small"
                  v-model:value="resetTime"
                  placeholder="自动归位时间间隔"
                  addonBefore="自动归位时间间隔"
                  addonAfter="(秒)"
                  class="ptz-space"
                />
                <a-button-group>
                  <a-button @click="setHomePositionStart()">启用</a-button>
                  <a-button @click="setHomePositionStop()">停用</a-button>
                </a-button-group>
              </div>
            </div>
          </a-tab-pane>
          <a-tab-pane key="3" tab="信息" style="padding: 0 1rem 0 1rem">
            <a-descriptions :column="1" title="资源地址" :labelStyle="{ fontsize: '12px' }">
              <a-descriptions-item>{{ playUrl }}</a-descriptions-item>
              <a-descriptions-item>
                <a-button size="small" @click="showMoreUrlHandler">更多地址</a-button>
              </a-descriptions-item>
            </a-descriptions>
            <a-descriptions :column="1" v-if="showMoreUrl" :labelStyle="{ fontsize: '12px' }">
              <a-descriptions-item label="FLV">{{ streamInfo.flv }}</a-descriptions-item>
              <a-descriptions-item label="FLV(https)">{{
                streamInfo.https_flv
              }}</a-descriptions-item>
              <a-descriptions-item label="FLV(ws)">{{ streamInfo.ws_flv }}</a-descriptions-item>
              <a-descriptions-item label="FLV(wss)">{{ streamInfo.wss_flv }}</a-descriptions-item>
              <a-descriptions-item label="FMP4">{{ streamInfo.fmp4 }}</a-descriptions-item>
              <a-descriptions-item label="FMP4(https)">{{
                streamInfo.https_fmp4
              }}</a-descriptions-item>
              <a-descriptions-item label="FMP4(ws)">{{ streamInfo.ws_fmp4 }}</a-descriptions-item>
              <a-descriptions-item label="FMP4(wss)">{{ streamInfo.wss_fmp4 }}</a-descriptions-item>
              <a-descriptions-item label="HLS">{{ streamInfo.hls }}</a-descriptions-item>
              <a-descriptions-item label="HLS(https)">{{
                streamInfo.https_hls
              }}</a-descriptions-item>
              <a-descriptions-item label="HLS(ws)">{{ streamInfo.ws_hls }}</a-descriptions-item>
              <a-descriptions-item label="HLS(wss)">{{ streamInfo.wss_hls }}</a-descriptions-item>
              <a-descriptions-item label="TS">{{ streamInfo.ts }}</a-descriptions-item>
              <a-descriptions-item label="TS(https)">{{ streamInfo.https_ts }}</a-descriptions-item>
              <a-descriptions-item label="TS(ws)">{{ streamInfo.ws_ts }}</a-descriptions-item>
              <a-descriptions-item label="TS(wss)">{{ streamInfo.wss_ts }}</a-descriptions-item>
              <a-descriptions-item label="RTC">{{ streamInfo.rtc }}</a-descriptions-item>
              <a-descriptions-item label="RTCS">{{ streamInfo.rtcs }}</a-descriptions-item>
              <a-descriptions-item label="RTMP">{{ streamInfo.rtmp }}</a-descriptions-item>
              <a-descriptions-item label="RTMPS">{{ streamInfo.rtmps }}</a-descriptions-item>
              <a-descriptions-item label="RTSP">{{ streamInfo.rtsp }}</a-descriptions-item>
              <a-descriptions-item label="RTSPS">{{ streamInfo.rtsps }}</a-descriptions-item>
            </a-descriptions>
            <a-descriptions :column="2" title="概况" :labelStyle="{ fontsize: '12px' }">
              <a-descriptions-item label="观看人数">{{ totalReaderCount }}</a-descriptions-item>
              <a-descriptions-item label="网络">{{ formatByteSpeed() }}</a-descriptions-item>
              <a-descriptions-item label="持续时间">{{ formatAliveSecond() }}</a-descriptions-item>
            </a-descriptions>
            <a-descriptions v-if="!!videoTrack" :column="2" title="视频信息">
              <a-descriptions-item label="编码">{{ videoTrack.codec_id_name }}</a-descriptions-item>
              <a-descriptions-item label="分辨率"
                >{{ videoTrack.width }}x{{ videoTrack.height }}
              </a-descriptions-item>
              <a-descriptions-item label="FPS">{{ videoTrack.fps }}</a-descriptions-item>
              <a-descriptions-item label="gop间隔">
                {{ videoTrack.gop_interval_ms }}ms
              </a-descriptions-item>
              <a-descriptions-item label="gop大小">
                {{ videoTrack.gop_size }}帧
              </a-descriptions-item>
              <a-descriptions-item label="关键帧数">
                {{ videoTrack.key_frames }}
              </a-descriptions-item>
              <a-descriptions-item label="丢包率">{{ videoTrack.loss }}</a-descriptions-item>
            </a-descriptions>
            <a-descriptions v-if="!!audioTrack" :column="2" title="音频信息" style="width: 100%">
              <a-descriptions-item label="编码">
                {{ audioTrack.codec_id_name }}
              </a-descriptions-item>
              <a-descriptions-item label="采样位数">
                {{ audioTrack.sample_bit }}
              </a-descriptions-item>
              <a-descriptions-item label="采样率">{{ audioTrack.sample_rate }}</a-descriptions-item>
              <a-descriptions-item label="丢包率">{{ audioTrack.loss }}</a-descriptions-item>
            </a-descriptions>
          </a-tab-pane>
        </a-tabs>
      </a-col>
    </a-row>
  </a-modal>
</template>
<script lang="ts" setup>
  import { StreamInfo, Track } from '@/api/model/baseModel'
  import { ref } from 'vue'
  import {
    Modal as AModal,
    Row as ARow,
    Col as ACol,
    Tabs as ATabs,
    TabPane as ATabPane,
    Descriptions as ADescriptions,
    DescriptionsItem as ADescriptionsItem,
    RadioGroup as ARadioGroup,
    RadioButton as ARadioButton,
    Select as ASelect,
    SelectOption as ASelectOption,
    InputNumber as AInputNumber,
    ButtonGroup as AButtonGroup,
    Button as AButton,
  } from 'ant-design-vue'
  import Jessibuca from '@/components/Player/module/jessibuca.vue'
  import RtcPlayer from './module/rtcPlayer.vue'
  import Ptz from './module/ptz.vue'

  const open = ref<boolean>(false)
  const showMoreUrl = ref<boolean>(false)
  const playerType = ref<any>('1')
  let playUrl = ref<String>('')
  let ptzControlType = ref<String>('1')
  let ptzPresetId = ref<String>('1')
  let ptzCruiseId = ref<String>('1')
  let ptzScanId = ref<String>('1')
  let ptzPresetIdForCruise = ref<String>('1')
  let ptzCruiseSpeed = ref<String>('1')
  let ptzCruiseStay = ref<String>('1')
  let scanAutoSpeed = ref<String>('1')
  let ptzAuxiliarySwitchId = ref<String>('2')
  let ptzPresetIdForHomePosition = ref<String>('1')
  let resetTime = ref<String>('1')
  let videoTrack = ref<Track>()
  let audioTrack = ref<Track>()
  let title = ref<String>()
  let timer = 0
  let streamInfo = ref<StreamInfo>()
  const jessibuca = ref()
  const rtcPlayer = ref()
  let presetLoading = ref<boolean>(true)
  let hideControlTab = ref<boolean>(false)
  let addCruiseSwitch = ref<boolean>(false)
  let setScanSwitch = ref<boolean>(false)
  let setCruiseSpeedSwitch = ref<boolean>(false)
  let setCruiseStaySwitch = ref<boolean>(false)
  let setScanAutoSpeedSwitch = ref<boolean>(false)
  // const presetList = ref<PresetItem[]>()
  const play = (streamInfoParam: StreamInfo, name: string, hideControl: boolean) => {
    title.value = name
    streamInfo.value = streamInfoParam
    if (hideControl) {
      hideControlTab.value = true
    } else {
      hideControlTab.value = false
    }
    if (streamInfoParam.tracks && streamInfoParam.tracks.length > 0) {
      for (let i = 0; i < streamInfoParam.tracks.length; i++) {
        if (streamInfoParam.tracks[i].codec_type == 0) {
          videoTrack.value = streamInfoParam.tracks[i]
        } else {
          audioTrack.value = streamInfoParam.tracks[i]
        }
      }
    }
    playerTypeChange()
    open.value = true
    timer = window.setInterval(() => {
      refreshStreamInfo()
    }, 1000)
  }

  const playerTypeChange = () => {
    if (streamInfo.value == null) {
      return
    }
    if (playerType.value == 1) {
      if (location.protocol === 'https:') {
        playUrl.value = streamInfo.value.wss_flv
      } else {
        playUrl.value = streamInfo.value.ws_flv
      }
    } else if (playerType.value == 2) {
      if (location.protocol === 'https:') {
        playUrl.value = streamInfo.value.rtcs
      } else {
        playUrl.value = streamInfo.value.rtc
      }
    } else if (playerType.value == 3) {
      if (location.protocol === 'https:') {
        playUrl.value = streamInfo.value.https_fmp4
      } else {
        playUrl.value = streamInfo.value.fmp4
      }
    }
  }
  // const presetQuery = (presetItemList: PresetItem[]) => {
  //   presetLoading.value = false
  //   if (presetItemList.length > 255) {
  //     presetList.value = presetItemList.slice(0, 255)
  //   } else {
  //     presetList.value = presetItemList
  //   }
  // }
  const emit = defineEmits([
    'ptzCamera',
    'presetControl',
    'cruiseControl',
    'scanControl',
    'wiperControl',
    'auxiliaryControl',
    'forceIframeControl',
    'homePositionControl',
  ])
  const ptzCamera = (comond: string, speed: number) => {
    emit('ptzCamera', comond, speed)
  }
  const gotoPreset = () => {
    emit('presetControl', ptzPresetId.value, 'goto')
  }
  const setPreset = () => {
    emit('presetControl', ptzPresetId.value, 'set')
  }
  const delPreset = () => {
    emit('presetControl', ptzPresetId.value, 'delete')
  }
  const startCruise = () => {
    emit('cruiseControl', ptzCruiseId.value, 'start')
  }
  const addCruise = () => {
    addCruiseSwitch.value = !addCruiseSwitch.value
    setScanSwitch.value = false
    setCruiseSpeedSwitch.value = false
    setCruiseStaySwitch.value = false
  }
  const delCruise = () => {
    emit('cruiseControl', ptzCruiseId.value, 'delete')
  }
  const setCruiseSpeed = () => {
    setCruiseSpeedSwitch.value = !setCruiseSpeedSwitch.value
    addCruiseSwitch.value = false
    setScanSwitch.value = false
    setCruiseStaySwitch.value = false
  }
  const setCruiseStay = () => {
    setCruiseStaySwitch.value = !setCruiseStaySwitch.value
    addCruiseSwitch.value = false
    setScanSwitch.value = false
    setCruiseSpeedSwitch.value = false
  }
  const addPresetForCruise = () => {
    emit(
      'cruiseControl',
      ptzCruiseId.value,
      'add',
      ptzPresetIdForCruise.value,
      undefined,
      undefined,
    )
  }
  const delPresetForCruise = () => {
    emit(
      'cruiseControl',
      ptzCruiseId.value,
      'delete',
      ptzPresetIdForCruise.value,
      undefined,
      undefined,
    )
  }
  const setCruiseSpeedForSave = () => {
    emit('cruiseControl', ptzCruiseId.value, 'setSpeed', undefined, ptzCruiseSpeed.value, undefined)
  }
  const setCruiseStayForSave = () => {
    emit('cruiseControl', ptzCruiseId.value, 'setStay', undefined, undefined, ptzCruiseStay.value)
  }
  const startScan = () => {
    emit('scanControl', 'start', ptzScanId.value, undefined)
  }

  const setScan = () => {
    setScanSwitch.value = !setScanSwitch.value
    setScanAutoSpeedSwitch.value = false
  }

  const setScanAutoSpeed = () => {
    setScanAutoSpeedSwitch.value = !setScanAutoSpeedSwitch.value
    setScanSwitch.value = false
  }

  const setScanAutoSpeedSwitchSave = () => {
    emit('scanControl', 'setSpeed', ptzScanId.value, scanAutoSpeed.value)
  }
  const setScanLeft = () => {
    emit('scanControl', 'setLeft', ptzScanId.value, undefined)
  }
  const setScanRight = () => {
    emit('scanControl', 'setRight', ptzScanId.value, undefined)
  }
  const startWiper = () => {
    emit('wiperControl', 'on')
  }
  const stopWiper = () => {
    emit('wiperControl', 'off')
  }
  const startAuxiliarySwitch = () => {
    emit('auxiliaryControl', 'on', ptzAuxiliarySwitchId.value)
  }
  const stopAuxiliarySwitch = () => {
    emit('auxiliaryControl', 'off', ptzAuxiliarySwitchId.value)
  }
  const startForceKeyframe = () => {
    emit('forceIframeControl')
  }
  const setHomePositionStart = () => {
    emit('homePositionControl', 'start', ptzPresetIdForHomePosition.value, resetTime.value)
  }
  const setHomePositionStop = () => {
    emit('homePositionControl', 'stop', ptzPresetIdForHomePosition.value, resetTime.value)
  }
  // 存活时间，单位秒
  let aliveSecond = ref<number>(0)
  // 观看总人数
  let totalReaderCount = ref<number>(0)
  // 数据产生速度，单位byte/s
  let bytesSpeed = ref<number>(0)
  const closeModel = () => {
    console.log('onBeforeUnmount')
    open.value = false
    playUrl.value = ''
    title.value = ''
    videoTrack.value = undefined
    audioTrack.value = undefined
    jessibuca.value = undefined
    rtcPlayer.value = undefined
    aliveSecond.value = 0
    totalReaderCount.value = 0
    bytesSpeed.value = 0
    window.clearInterval(timer)
  }

  const refreshStreamInfo = () => {
    if (streamInfo.value == null) {
      return
    }
    // getMediaInfoApi(streamInfo.value.mediaServerId, streamInfo.value.app, streamInfo.value.stream)
    //   .then((result) => {
    //     let streamInfoParam = result as StreamInfo
    //     if (streamInfoParam.tracks && streamInfoParam.tracks.length > 0) {
    //       for (let i = 0; i < streamInfoParam.tracks.length; i++) {
    //         if (streamInfoParam.tracks[i].codec_type == 0) {
    //           videoTrack.value = streamInfoParam.tracks[i]
    //         } else {
    //           audioTrack.value = streamInfoParam.tracks[i]
    //         }
    //       }
    //     }
    //     aliveSecond.value = streamInfoParam.aliveSecond
    //     totalReaderCount.value = streamInfoParam.totalReaderCount
    //     bytesSpeed.value = streamInfoParam.bytesSpeed
    //   })
    //   .catch((e) => {
    //     console.error(e)
    //   })
  }

  const formatByteSpeed = () => {
    var num = 1024.0 //byte
    if (bytesSpeed.value < num) return bytesSpeed.value + ' B/S'
    if (bytesSpeed.value < Math.pow(num, 2)) return (bytesSpeed.value / num).toFixed(2) + ' KB/S' //kb
    if (bytesSpeed.value < Math.pow(num, 3))
      return (bytesSpeed.value / Math.pow(num, 2)).toFixed(2) + ' MB/S' //M
    if (bytesSpeed.value < Math.pow(num, 4))
      return (bytesSpeed.value / Math.pow(num, 3)).toFixed(2) + ' G/S' //G
    return (bytesSpeed.value / Math.pow(num, 4)).toFixed(2) + ' T/S' //T
  }

  const formatAliveSecond = () => {
    const h = parseInt(aliveSecond.value / 3600)
    const minute = parseInt((aliveSecond.value / 60) % 60)
    const second = Math.ceil(aliveSecond.value % 60)

    const hours = h < 10 ? '0' + h : h
    const formatSecond = second > 59 ? 59 : second
    return `${hours > 0 ? `${hours}小时` : ''}${minute < 10 ? '0' + minute : minute}分${
      formatSecond < 10 ? '0' + formatSecond : formatSecond
    }秒`
  }

  const showMoreUrlHandler = () => {
    showMoreUrl.value = !showMoreUrl.value
  }

  defineExpose({ play })
</script>
<style>
  #mediaInfo {
    width: 30%;
    height: 90%;
    position: absolute;
    display: -webkit-box;
    display: -ms-flexbox;
    background: #1a1a1a;
    left: 0;
    top: 0;
    user-select: none;
    z-index: 10;
    padding: 1rem;
    overflow: scroll;
    opacity: 0.7;
  }
  .ant-descriptions-title {
    flex: auto;
    overflow: hidden;
    color: rgba(0, 0, 0, 0.85);
    font-weight: bold;
    font-size: 14px;
    line-height: 1.2;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
  .ant-descriptions-item-label {
    color: rgba(0, 0, 0, 0.85);
    font-weight: normal;
    font-size: 12px;
    line-height: 1;
    text-align: start;
  }
  .ant-descriptions-item-content {
    flex: 1;
    color: rgba(0, 0, 0, 0.85);
    font-size: 12px;
    line-height: 1;
    word-break: break-word;
    overflow-wrap: break-word;
  }
  .preset-btn {
    font-size: 12px;
    padding-right: 10px;
  }
  .preset-danger {
    color: #ed6f6f;
    padding-right: 0;
  }
  .ptz-space {
    width: 100%;
    margin-bottom: 1rem;
  }
</style>
