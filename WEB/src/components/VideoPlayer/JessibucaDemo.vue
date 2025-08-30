<template>
  <div class="root">
    <div class="container-shell">
      <div class="container-shell-title">jessibuca demo player</div>
      <div id="container" ref="container"></div>
      <div class="input">
        <div>输入URL：</div>
        <input
          type="input"
          autocomplete="on"
          :value="playUrl"
        />
        <button v-if="!playing" @click="play">播放</button>
        <button v-else @click="pause">停止</button>
      </div>
      <div class="input" v-if="loaded">
        <button @click="destroy">销毁</button>

      </div>
    </div>
  </div>
</template>

<script lang="ts">
// @ts-nocheck
import {ref} from "vue";
import {onMounted, onUnmounted} from "vue";

export default {
  name: "JessibucaDemo",
  setup() {
    let jessibuca = null;
    const container = ref(null);
    const buffer = ref(null);
    const showBandwidth = ref(false)
    const showOperateBtns = ref(false);
    const forceNoOffscreen = ref(false);
    const playUrl = ref('https://live.nodemedia.cn:8443/live/b480_264.flv');
    const playing = ref(false);
    const quieting = ref(true);
    const loaded = ref(false);
    const createJessibuca = () => {
      // eslint-disable-next-line
      jessibuca = new (window as any).Jessibuca({
        container: container.value,
        videoBuffer: 0.2, // 缓存时长
        isResize: false,
        text: "",
        // background: "bg.jpg",
        loadingText: "加载中",
        // hasAudio:false,
        debug: true,
        showBandwidth: showBandwidth.value, // 显示网速
        operateBtns: {
          fullscreen: showOperateBtns.value,
          screenshot: showOperateBtns.value,
          play: showOperateBtns.value,
          audio: showOperateBtns.value,
        },
        forceNoOffscreen: forceNoOffscreen.value,
        isNotMute: false,
      }) as Jessibuca

      jessibuca.on("load", function () {
        console.log("on load");
      });

      jessibuca.on("log", function (msg: any) {
        console.log("on log", msg);
      });
      jessibuca.on("record", function (msg: any) {
        console.log("on record:", msg);
      });
      jessibuca.on("pause", function () {
        console.log("on pause");
        playing.value = false;
      });
      jessibuca.on("play", function () {
        console.log("on play");
        playing.value = true;
        loaded.value = true;
        quieting.value = jessibuca.isMute();
      });
      jessibuca.on("fullscreen", function (msg: any) {
        console.log("on fullscreen", msg);
      });

      jessibuca.on("mute", function (msg: any) {
        console.log("on mute", msg);
        quieting.value = msg;
      });

      jessibuca.on("mute", function (msg: any) {
        console.log("on mute2", msg);
      });

      jessibuca.on("audioInfo", function (msg: any) {
        console.log("audioInfo", msg);
      });

      // jessibuca.on("bps", function (bps) {
      //   // console.log('bps', bps);
      // });
      // let _ts = 0;
      // jessibuca.on("timeUpdate", function (ts) {
      //   // console.log('timeUpdate,old,new,timestamp', _ts, ts, ts - _ts);
      //   // _ts = ts;
      // });

      jessibuca.on("videoInfo", function (info: any) {
        console.log("videoInfo", info);
      });

      jessibuca.on("error", function (error: any) {
        console.log("error", error);
      });

      jessibuca.on("timeout", function () {
        console.log("timeout");
      });

      jessibuca.on('start', function () {
        console.log('start');
      })

      // jessibuca.on("stats", function (stats) {
      //   console.log('stats', JSON.stringify(stats));
      // });

      jessibuca.on("performance", function (performance: any) {
        var show = "卡顿";
        if (performance === 2) {
          show = "非常流畅";
        } else if (performance === 1) {
          show = "流畅";
        }
      });
      jessibuca.on('buffer', function (buffer: any) {
        console.log('buffer', buffer);
      })

      jessibuca.on('stats', function (stats: any) {
        console.log('stats', stats);
      })

      jessibuca.on('kBps', function (kBps: any) {
        console.log('kBps', kBps);
      });

      // 显示时间戳 PTS
      jessibuca.on('videoFrame', function () {

      })

      //
      jessibuca.on('metadata', function () {

      });


    }

    onMounted(() => {
      createJessibuca();
    })

    onUnmounted(async () => {
      if (jessibuca) {
        await jessibuca && jessibuca.destroy();
        jessibuca = null;
      }
    })

    const play = () => {
      if (playUrl.value) {
        jessibuca.play(playUrl.value);
      }
    }
    const pause = () => {
      jessibuca.pause();
      playing.value = false;
    }

    const destroy = async () => {
      if (jessibuca) {
        await jessibuca.destroy();
        jessibuca = null;
      }
      createJessibuca();
      playing.value = false;
      loaded.value = false;
    }

    return {
      container,
      buffer,
      showBandwidth,
      playing,
      playUrl,
      play,
      pause,
      destroy,
      loaded
    }


  }
}
</script>

<style>
.root {
  display: flex;
  place-content: center;
  margin-top: 3rem;
}

.container-shell {
  position: relative;
  backdrop-filter: blur(5px);
  background: hsla(0, 0%, 50%, 0.5);
  padding: 30px 4px 10px 4px;
  /* border: 2px solid black; */
  width: auto;
  position: relative;
  border-radius: 5px;
  box-shadow: 0 10px 20px;
}

.container-shell-title {
  position: absolute;
  color: darkgray;
  top: 4px;
  left: 10px;
  text-shadow: 1px 1px black;
}

.tag-version {
}

#container {
  background: rgba(13, 14, 27, 0.7);
  width: 640px;
  height: 398px;
}

.input {
  display: flex;
  align-items: center;
  margin-top: 10px;
  color: white;
  place-content: stretch;
}

.input2 {
  bottom: 0px;
}

.input input[type='input'] {
  flex: auto;
}

.err {
  position: absolute;
  top: 40px;
  left: 10px;
  color: red;
}

.option {
  position: absolute;
  top: 4px;
  right: 10px;
  display: flex;
  place-content: center;
  font-size: 12px;
}

.option span {
  color: white;
}

@media (max-width: 720px) {
  #container {
    width: 90vw;
    height: 52.7vw;
  }
}
</style>
