<template>
  <div id="rtcPlayer" style="width: 100%; height: 100%; background-color: #000c17">
    <video id="webRtcPlayerBox" controls autoplay style="text-align: left">
      Your browser is too old which doesn't support HTML5 video.
    </video>
  </div>
</template>

<script lang="ts" setup>
  // @ts-nocheck
  import { onMounted, onUnmounted, watch } from 'vue'

  let timer: number
  let webrtcPlayer: any
  const props = defineProps({
    playUrl: {
      type: String,
      required: true,
    },
    hasAudio: {
      type: Boolean,
      required: true,
    },
  })
  watch(
    () => props.playUrl,
    (newPlayerUrl) => {
      console.log('watch== ' + newPlayerUrl)
      pause()
      play(newPlayerUrl)
    },
  )
  onMounted(() => {
    console.log('播放器拿到的地址： ' + props.playUrl)
    if (props.playUrl) {
      play(props.playUrl)
    }
  })
  const play = (url: string) => {
    console.log('rtc-plau: ' + url)
    console.log(url)
    webrtcPlayer = new (window as any).ZLMRTCClient.Endpoint({
      element: document.getElementById('webRtcPlayerBox'),
      debug: true,
      zlmsdpUrl: url,
      simulecast: false,
      useCamera: false,
      audioEnable: false,
      videoEnable: false,
      recvOnly: true,
      resolution: [1920, 1080],
      usedatachannel: false,
    })
    webrtcPlayer.on((window as any).ZLMRTCClient.Events.WEBRTC_ICE_CANDIDATE_ERROR, (e) => {
      // ICE 协商出错
      console.error('ICE 协商出错')
      eventcallbacK('ICE ERROR', 'ICE 协商出错' + e.toString())
    })

    webrtcPlayer.on((window as any).ZLMRTCClient.Events.WEBRTC_ON_REMOTE_STREAMS, (e) => {
      //获取到了远端流，可以播放
      console.log('播放成功', e.streams)
      eventcallbacK('playing', '播放成功')
    })

    webrtcPlayer.on(
      (window as any).ZLMRTCClient.Events.WEBRTC_OFFER_ANWSER_EXCHANGE_FAILED,
      (e) => {
        console.error('offer anwser 交换失败', e)
        eventcallbacK('OFFER ANSWER ERROR ', 'offer anwser 交换失败')
        if (e.code == -400 && e.msg == '流不存在') {
          console.log('流不存在')
          timer = window.setTimeout(() => {
            webrtcPlayer.close()
            play(url)
          }, 100)
        }
      },
    )

    webrtcPlayer.on((window as any).ZLMRTCClient.Events.WEBRTC_ON_LOCAL_STREAM, () => {
      // 获取到了本地流
      // document.getElementById('selfVideo').srcObject=s;
      eventcallbacK('LOCAL STREAM', '获取到了本地流')
    })
  }

  const eventcallbacK = (type, message) => {
    console.log('player 事件回调')
    console.log(type)
    console.log(message)
  }

  const pause = () => {
    if (webrtcPlayer != null) {
      webrtcPlayer.close()
      webrtcPlayer = null
    }
  }

  onUnmounted(() => {
    clearTimeout(timer)
    pause()
  })
</script>
