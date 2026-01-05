<template>
  <div class="app-container main-div">
    <EasyPlayer
      :videoUrl="videoUrls"
      lineType="fourWays"
    ></EasyPlayer>
  </div>
</template>

<script setup name="Index">
import {ref} from "vue";
import EasyPlayer from "./EasyPlayer.vue";

defineOptions({name: 'Player'})

const videoUrls = ref([
  "http://192.168.1.102:800/live/test.flv",
  "http://192.168.1.102:800/live/test1.flv",
  "http://192.168.1.102:800/live/test2.flv",
  "http://192.168.1.102:800/live/test.flv",
  "http://192.168.1.102:800/live/test.flv",
  "http://192.168.1.102:800/live/test.flv",
  "http://192.168.1.102:800/live/test.flv",
  "http://192.168.1.102:800/live/test.flv",
  "http://192.168.1.102:800/live/test.flv",
  "http://192.168.1.102:800/live/test.flv",
  "http://192.168.1.102:800/live/test.flv",
  "http://192.168.1.102:800/live/test.flv",
  "http://192.168.1.102:800/live/test.flv",
  "http://192.168.1.102:800/live/test.flv",
  "http://192.168.1.102:800/live/test.flv",
  "http://192.168.1.102:800/live/test.flv",
]);
</script>

<style scoped lang="less">
.main-div {
  padding: 0 !important;
}
</style>

