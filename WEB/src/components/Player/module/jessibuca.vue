<template>
  <div
    :class="{
      'jessibuca-root--vod': vodMode,
      'jessibuca-root--fill': fillVideo && !vodMode,
    }"
    class="jessibuca-root"
    style="width: 100%; height: 100%; background-color: #000"
  >
    <div ref="container" class="jessibuca-container" @dblclick="fullscreen" @mousemove="mouseenter">
      <transition name="toolBtn">
        <div
          v-if="showToolBtn"
          class="buttons-box"
          id="buttonsBox"
          @mouseenter="keepShowTool"
          @mousemove="
            (e) => {
              e.stopPropagation()
            }
          "
          @mouseleave="mouseenter"
        >
          <div class="buttons-box-left">
            <Icon
              v-if="!playing"
              :size="iconSize"
              class="jessibuca-btn"
              icon="ic:baseline-play-arrow"
              @click="play"
            />
            <Icon
              :size="iconSize"
              v-if="playing"
              class="jessibuca-btn"
              icon="ic:baseline-pause"
              @click="pause"
            />
            <Icon
              :size="iconSize"
              icon="ic:baseline-stop"
              class="jessibuca-btn"
              @click="destroy"
            />
            <Icon
              :size="iconSize"
              v-if="!quieting"
              icon="ic:baseline-volume-up"
              class="jessibuca-btn"
              @click="mute"
            />
            <Icon
              :size="iconSize"
              v-if="quieting"
              icon="ic:baseline-volume-off"
              class="jessibuca-btn"
              @click="cancelMute"
            />
          </div>
          <div class="buttons-box-right">
            <span class="jessibuca-btn">{{ kbs }} kb/s</span>
            <Icon
              :size="iconSize"
              icon="ic:baseline-camera"
              class="jessibuca-btn"
              @click="screenShot"
            />
            <Icon
              v-if="!recording"
              :size="iconSize"
              icon="tabler:video"
              class="jessibuca-btn"
              @click="startRecord"
            />
            <Icon
              v-if="recording"
              :size="iconSize"
              icon="fluent-emoji-flat:stop-sign"
              class="jessibuca-btn"
              @click="stopAndSaveRecord"
            />
            <Icon
              :size="iconSize"
              v-if="!isFull"
              icon="ic:baseline-fullscreen"
              class="jessibuca-btn"
              @click="fullscreen"
            />
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script>

import {Icon} from "@/components/Icon";
import {ref} from "vue";
import {signStreamUrl, isProtectedStreamUrl, clearTicketForUrl} from "@/views/camera/utils/streamTicket";
import {rewriteStreamHostToPageHost, normalizeJessibucaPlayUrl, isAiStreamPlayUrl, AI_STREAM_LOAD_TIMEOUT_SEC, AI_STREAM_HEART_TIMEOUT_SEC} from "@/views/camera/utils/devicePlay";

/** 实时预览超时（秒）：过短会在网络轻微抖动时频繁重连，导致卡顿黑屏 */
const LIVE_TIMEOUT_SEC = 30;
const LIVE_HEART_TIMEOUT_SEC = 60;
const LIVE_REPLAY_TIMES = 5;

/** 切流/卸载/浏览器省电策略导致的播放中断，无需向用户报错 */
function isBenignPlayerError(e) {
  if (!e) return true;
  const name = e?.name || "";
  const msg = String(e?.message || e || "").toLowerCase();
  return (
    name === "AbortError" ||
    name === "CanceledError" ||
    msg.includes("postmessage") ||
    msg.includes("play() request was interrupted") ||
    msg.includes("background media was paused")
  );
}

export default {
  name: "Player",
  components: {Icon},
  emits: ["stream-error"],
  props: {
    playUrl: {
      type: String,
      required: true,
    },
    hasAudio: {
      type: Boolean,
      required: true,
    },
    /** 点播/录像文件（非实时流），需放宽超时并启用 isFlv */
    vodMode: {
      type: Boolean,
      default: false,
    },
    /** 实时预览铺满容器（与录像回放一致） */
    fillVideo: {
      type: Boolean,
      default: false,
    },
    /** 多分屏场景：优先 MSE 硬解，减轻多路 WASM 软解卡顿 */
    multiView: {
      type: Boolean,
      default: false,
    },
    /** 当前为 /ai 流且可回退 /live 时，缩短加载超时以便上层快速无感切换 */
    aiWithFallback: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      jessibuca: null,
      version: '',
      wasm: false,
      vc: "ff",
      playing: false,
      quieting: true,
      loaded: false, // mute
      showOperateBtns: false,
      showBandwidth: false,
      err: "",
      speed: 0,
      performance: "",
      volume: 1,
      rotate: 0,
      useWCS: false,
      useMSE: true,
      useOffscreen: false,
      recording: false,
      recordType: 'mp4',
      scale: 0,
      iconSize: 16,
      showToolBtnTimer: 0,
      showToolBtn: false,
      kbs: 0,
      isFull: false,
      // 受保护流(secure_link)票据过期/报错时的静默续票重试计数
      protectedRetries: 0,
      maxProtectedRetries: 2,
      vodResizeObserver: null,
      _vodResizeTimer: null,
      _unmounting: false,
      _onUnhandledRejection: null,
    };
  },
  beforeUnmount() {
    this._unmounting = true;
    if (this._vodResizeTimer) {
      window.clearTimeout(this._vodResizeTimer);
      this._vodResizeTimer = null;
    }
    this.unbindVodResizeObserver();
    if (this._onUnhandledRejection) {
      window.removeEventListener("unhandledrejection", this._onUnhandledRejection);
      this._onUnhandledRejection = null;
    }
  },
  mounted() {
    this.create();
    window.onerror = (msg) => (this.err = msg);
    this._onUnhandledRejection = (event) => {
      if (isBenignPlayerError(event?.reason)) {
        event.preventDefault();
      }
    };
    window.addEventListener("unhandledrejection", this._onUnhandledRejection);
    if (this.playUrl) {
      this.$nextTick(() => this.play());
    }
    if (this.shouldFillContainer()) {
      this.bindVodResizeObserver();
    }
  },
  watch: {
    playUrl(url, oldUrl) {
      this.protectedRetries = 0;
      if (!url || !this.jessibuca) return;
      // 同实例切流即可，勿 destroy 重建（多分屏切 /ai 时 destroy 会导致卡死黑屏）
      if (oldUrl && url !== oldUrl) {
        const nextFast = this.shouldAiFastFail(url);
        const prevFast = this.shouldAiFastFail(oldUrl);
        if (nextFast !== prevFast) {
          this.destroy().then(() => this.$nextTick(() => this.play(true)));
        } else {
          this.$nextTick(() => this.play(true));
        }
      }
    },
    vodMode() {
      this.handleDisplayModeChange();
    },
    fillVideo() {
      this.handleDisplayModeChange();
    },
  },
  async unmounted() {
    if (this.jessibuca) {
      await this.safeDestroyJessibuca();
      this.jessibuca = null;
    }
  },
  methods: {
    async safeDestroyJessibuca() {
      const inst = this.jessibuca;
      if (!inst) return;
      try {
        if (typeof inst.pause === "function") {
          try {
            inst.pause();
          } catch {
            /* ignore */
          }
        }
        await inst.destroy();
      } catch (e) {
        if (!isBenignPlayerError(e)) {
          console.warn("jessibuca destroy error", e);
        }
      }
    },
    shouldFillContainer() {
      return this.vodMode === true || this.fillVideo === true;
    },
    /** 0 拉伸铺满 | 1 等比缩放(留黑边) | 2 等比裁剪铺满 */
    getScaleMode() {
      if (this.vodMode || this.fillVideo) return 0;
      return 1;
    },
    handleDisplayModeChange() {
      if (this.jessibuca) {
        this.destroy().then(() => {
          this.create();
          if (this.playUrl) this.$nextTick(() => this.play());
        });
      }
      if (this.shouldFillContainer()) {
        this.$nextTick(() => this.bindVodResizeObserver());
      } else {
        this.unbindVodResizeObserver();
      }
    },
    bindVodResizeObserver() {
      this.unbindVodResizeObserver();
      const el = this.$refs.container;
      if (!el || typeof ResizeObserver === 'undefined') return;
      this.vodResizeObserver = new ResizeObserver(() => {
        this.scheduleVodResize();
      });
      this.vodResizeObserver.observe(el);
      if (el.parentElement) {
        this.vodResizeObserver.observe(el.parentElement);
      }
    },
    unbindVodResizeObserver() {
      if (this.vodResizeObserver) {
        this.vodResizeObserver.disconnect();
        this.vodResizeObserver = null;
      }
    },
    scheduleVodResize() {
      if (!this.shouldFillContainer() || !this.jessibuca) return;
      if (this._vodResizeTimer) {
        window.clearTimeout(this._vodResizeTimer);
      }
      const scaleMode = this.getScaleMode();
      const run = () => {
        if (!this.jessibuca || !this.playing) return;
        try {
          this.jessibuca.setScaleMode(scaleMode);
          if (typeof this.jessibuca.resize === 'function') {
            this.jessibuca.resize();
          }
        } catch {
          /* 解码器尚未初始化 */
        }
      };
      this._vodResizeTimer = window.setTimeout(() => {
        this._vodResizeTimer = null;
        run();
      }, 120);
    },
    shouldAiFastFail(url) {
      const target = url || this.playUrl;
      return this.aiWithFallback === true && isAiStreamPlayUrl(target);
    },
    create(options) {
      options = options || {};
      const pageHttps =
        typeof window !== 'undefined' && window.location.protocol === 'https:';
      const vod = this.vodMode === true;
      const fill = this.shouldFillContainer();
      const stretchFill = vod || this.fillVideo === true;
      const scaleMode = this.getScaleMode();
      const protectedStream = isProtectedStreamUrl(this.playUrl);
      const isFlvStream = vod || /\.flv(\?|$)/i.test(this.playUrl || '');
      const useLiveMse = !vod && this.multiView === true;
      const aiFastFail = !vod && this.shouldAiFastFail(this.playUrl);
      // 受保护流禁止 Jessibuca 同地址自动重放（会复用过期 secure_link 票据），改由 maybeRenewOnError 续票重连
      const allowAutoReplay = vod || (!protectedStream && !aiFastFail);
      const liveTimeoutSec = aiFastFail ? AI_STREAM_LOAD_TIMEOUT_SEC : LIVE_TIMEOUT_SEC;
      const liveHeartSec = aiFastFail ? AI_STREAM_HEART_TIMEOUT_SEC : LIVE_HEART_TIMEOUT_SEC;
      this.jessibuca = new window.Jessibuca(
        Object.assign(
          {
            container: this.$refs.container,
            decoder: '/static/js/jessibuca/decoder.js',
            videoBuffer: vod ? 0.5 : 0.3,
            isResize: !stretchFill,
            isFullResize: false,
            isFlv: isFlvStream,
            hasAudio: this.hasAudio,
            // 多分屏/铺满：MSE 硬解 H.264；单路弹窗仍可用 WASM
            useWCS: false,
            useMSE: vod ? false : useLiveMse,
            autoWasm: true,
            hiddenAutoPause: false,
            keepScreenOn: true,
            text: "",
            loadingText: vod ? "录像加载中..." : "疯狂加载中...",
            debug: false,
            supportDblclickFullscreen: true,
            showBandwidth: this.showBandwidth,
            operateBtns: {
              fullscreen: this.showOperateBtns,
              screenshot: this.showOperateBtns,
              play: this.showOperateBtns,
              audio: this.showOperateBtns,
            },
            forceNoOffscreen: !this.useOffscreen,
            isNotMute: true,
            timeout: vod ? 60 : liveTimeoutSec,
            loadingTimeout: vod ? 60 : liveTimeoutSec,
            heartTimeout: vod ? 120 : liveHeartSec,
            loadingTimeoutReplay: allowAutoReplay,
            heartTimeoutReplay: allowAutoReplay,
            loadingTimeoutReplayTimes: LIVE_REPLAY_TIMES,
            heartTimeoutReplayTimes: LIVE_REPLAY_TIMES,
            wasmDecodeErrorReplay: true,
            openWebglAlignment: true,
          },
          options
        )
      );
      var _this = this;
      this.jessibuca.on("pause", function () {
        _this.playing = false;
      });
      this.jessibuca.on("play", function () {
        _this.playing = true;
        _this.protectedRetries = 0; // 成功起播，重置续票重试计数
        if (fill) {
          _this.jessibuca.setScaleMode(scaleMode);
          _this.scheduleVodResize();
        }
      });
      this.jessibuca.on("mute", function (msg) {
        _this.quieting = msg;
      });
      // this.jessibuca.on("bps", function (bps) {
      //   // console.log('bps', bps);
      // });
      // let _ts = 0;
      // this.jessibuca.on("timeUpdate", function (ts) {
      //     console.log('timeUpdate,old,new,timestamp', _ts, ts, ts - _ts);
      //     _ts = ts;
      // });
      this.jessibuca.on("videoInfo", function (info) {
        if (fill) {
          _this.jessibuca.setScaleMode(scaleMode);
          _this.scheduleVodResize();
        }
      });
      this.jessibuca.on("error", function (error) {
        if (_this.maybeRenewOnError()) return;
        _this.$emit("stream-error", { type: "error", detail: error });
      });
      this.jessibuca.on("timeout", function () {
        if (_this.maybeRenewOnError()) return;
        _this.$emit("stream-error", { type: "timeout" });
      });
      this.jessibuca.on("loadingTimeout", function () {
        if (_this.maybeRenewOnError()) return;
        _this.$emit("stream-error", { type: "loadingTimeout" });
      });
      this.jessibuca.on("delayTimeout", function () {
        if (_this.maybeRenewOnError()) return;
        _this.$emit("stream-error", { type: "delayTimeout" });
      });
      this.jessibuca.on("performance", function (performance) {
        var show = "卡顿";
        if (performance === 2) {
          show = "非常流畅";
        } else if (performance === 1) {
          show = "流畅";
        }
        _this.performance = show;
      });
      this.jessibuca.on('kBps', function (kBps) {
        _this.kbs = Math.round(kBps)
      });
      this.jessibuca.on("play", () => {
        this.playing = true;
        this.loaded = true;
        this.quieting = this.jessibuca.isMute();
        if (fill) {
          this.jessibuca.setScaleMode(scaleMode);
          this.scheduleVodResize();
        }
      });
    },
    async play(forceRefresh = false) {
      // 模板 @click="play" 会把鼠标事件当参数传入，这里归一为布尔，避免手动点播时被误判为强制续票
      const force = forceRefresh === true;
      if (!this.jessibuca && this.$refs.container) {
        this.create();
      }
      if (!this.playUrl || !this.jessibuca) return;

      const originalPlayUrl = this.playUrl;
      // 多分屏：上层已在 localhost/127.0.0.1:页面端口 间轮询（走 Vite /live 反代），
      // 禁止再统一改回单一页面 host，否则会撞上 HTTP/1.1 同 origin 约 6 路限制。
      // 单路预览仍改写到页面 host。
      let target = this.multiView
        ? originalPlayUrl
        : normalizeJessibucaPlayUrl(rewriteStreamHostToPageHost(originalPlayUrl));
      // 受保护流(/ai /live /rtp)需带 secure_link 票据，未签名会被 nginx 403
      if (isProtectedStreamUrl(target)) {
        try {
          target = await signStreamUrl(target, { forceRefresh: force });
        } catch (e) {
          // 签发失败(mint 不可用/网络/会话过期)：降级用未签名地址尽力播放，
          // 不把整路播放卡死在签发服务上：强制校验关闭时仍可播；开启时会 403 ->
          // on('error') -> maybeRenewOnError 再续票自愈；若是 401，axios 已统一跳登录。
          console.warn("stream ticket sign failed, fallback to unsigned url", e);
          target = this.multiView
            ? this.playUrl
            : normalizeJessibucaPlayUrl(rewriteStreamHostToPageHost(this.playUrl));
        }
        // 防竞态：等待签发期间地址已切换/组件已销毁则放弃
        if (this.playUrl !== originalPlayUrl || !this.jessibuca) return;
      }
      this.jessibuca.play(target);
      if ((this.vodMode || this.fillVideo) && this.jessibuca) {
        this.jessibuca.setScaleMode(0);
        this.scheduleVodResize();
      }
    },
    // 受保护流报错(多为票据过期/连接被关)时：强制重新签发并重连，限次防死循环。
    // 返回 true 表示已接管(吞掉本次错误)，false 表示交回上层 emit stream-error。
    maybeRenewOnError() {
      if (!isProtectedStreamUrl(this.playUrl)) return false;
      if (this.protectedRetries >= this.maxProtectedRetries) return false;
      this.protectedRetries++;
      clearTicketForUrl(this.playUrl);
      this.play(true);
      return true;
    },
    mute() {
      this.jessibuca.mute();
    },
    cancelMute() {
      this.jessibuca.cancelMute();
    },
    pause() {
      this.jessibuca.pause();
      this.playing = false;
      this.err = "";
      this.performance = "";
    },
    volumeChange() {
      this.jessibuca.setVolume(this.volume);
    },
    rotateChange() {
      this.jessibuca.setRotate(this.rotate);
    },
    async destroy() {
      if (this.jessibuca) {
        await this.safeDestroyJessibuca();
        this.jessibuca = null;
      }
      // 仅当容器仍在且组件未卸载(切流复用)时才重建
      if (!this._unmounting && this.$refs.container) {
        this.create();
      }
      this.playing = false;
      this.loaded = false;
      this.performance = "";
    },
    fullscreen() {
      this.jessibuca.setFullscreen(true);
    },
    clearView() {
      this.jessibuca.clearView();
    },
    startRecord() {
      this.recording = !this.recording;
      const time = new Date().getTime();
      this.jessibuca.startRecord(time, this.recordType);
    },
    stopAndSaveRecord() {
      this.recording = !this.recording;
      this.jessibuca.stopRecordAndSave();
    },
    screenShot() {
      this.jessibuca.screenshot();
    },
    mouseenter() {
      this.showToolBtn = true
      if (this.showToolBtnTimer) {
        window.clearTimeout(this.showToolBtnTimer)
      }
      this.showToolBtnTimer = window.setTimeout(() => {
        this.showToolBtn = false
      }, 4000)
    },
    keepShowTool() {
      this.showToolBtn = true
      window.clearTimeout(this.showToolBtnTimer)
    },
    isFullscreen() {
      return document.fullscreenElement || false
    },
    async restartPlay(type) {
      if (type === 'mse') {
        this.useWCS = false;
        this.useOffscreen = false;
      } else if (type === 'wcs') {
        this.useMSE = false
      } else if (type === 'offscreen') {
        this.useMSE = false
      }
      await this.destroy();
      setTimeout(() => {
        this.play();
      }, 100)
    },
    changeBuffer() {
      this.jessibuca.setBufferTime(Number(0.2));
    },
    scaleChange() {
      this.jessibuca.setScaleMode(this.scale);
    },
  },
};
</script>

<style>
.buttons-box {
  width: 100%;
  height: 28px;
  background-color: rgba(43, 51, 63, 0.7);
  position: absolute;
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
  left: 0;
  bottom: 0;
  user-select: none;
  z-index: 10;
  transition: opacity 1s ease;
}

.jessibuca-btn {
  width: 20px;
  color: rgb(255, 255, 255);
  line-height: 28px;
  margin: 0px 10px;
  padding: 0px 2px;
  cursor: pointer;
  text-align: center;
  font-size: 1rem !important;
}

.buttons-box-right {
  position: absolute;
  right: 0;
}

.toolBtn-enter-active {
  transition: all 0.1s;
  overflow: hidden;
}

.toolBtn-leave-active {
  transition: all 0.5s;
  overflow: hidden;
}

.toolBtn-enter-from,
.toolBtn-leave-to {
  height: 0px !important;
  opacity: 0;
}

.jessibuca-root {
  display: block;
}

.jessibuca-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.jessibuca-root--fill .jessibuca-container canvas,
.jessibuca-root--fill .jessibuca-container video {
  position: absolute !important;
  left: 0 !important;
  top: 0 !important;
  width: 100% !important;
  height: 100% !important;
  max-width: none !important;
  max-height: none !important;
  transform: none !important;
}

.jessibuca-container video {
  max-height: 100%;
}
</style>
