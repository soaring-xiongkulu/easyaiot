<template>
  <div data-v-13877386="" id="devicePosition" style="width: 100vw; height: 82vh;">
    <section class="el-container" element-loading-text="拼命加载中" style="height: 82vh;">
      <aside class="el-aside" style="width: 300px; background-color: rgb(255, 255, 255);">
        <div id="DeviceTree"
             style="width: 100%; height: 100%; background-color: rgb(255, 255, 255); overflow: auto;">
          <section class="el-container is-vertical">
            <header class="el-header" style="height: 60px;">设备列表</header>
            <main class="el-main" style="background-color: rgb(255, 255, 255);">
              <div class="device-tree-main-box">
                <BasicTree
                  ref="treeRef"
                  search
                  :showIcon="true"
                  v-model:selectedKeys="selectedKeys"
                  @select="handleSelect"
                  :tree-data="treeData"
                  :load-data="onLoadData"
                  :field-names="{ key: 'deviceId', title: 'name' }"
                >
                </BasicTree>
              </div>
            </main>
          </section>
        </div>
      </aside>
      <section :class="{ full: state.isFull }" class="el-container is-vertical">
        <header class="el-header"
                style="height: 5vh; text-align: left; font-size: 17px; line-height: 5vh; background-color: #ffffff">
          分屏:
          <Icon :class="{ active: state.isActive[0] }" :onclick="handleGridChange.bind(null, 0)"
                icon="akar-icons:full-screen"/>
          <Icon :class="{ active: state.isActive[1] }" :onclick="handleGridChange.bind(null, 1)"
                icon="ic:sharp-grid-view"/>
          <Icon :class="{ active: state.isActive[2] }" :onclick="handleGridChange.bind(null, 2)"
                icon="bi:grid-3x3-gap-fill"/>
          <Icon :class="{ active: state.isActive[3] }" :onclick="handleGridChange.bind(null, 3)"
                icon="material-symbols:background-grid-small"/>
          <span style="margin: 0 20px"></span>
          操作：
          <Button type="primary" :onclick="handleGridDelete.bind(null)" style="margin-right: 20px">
            选中删除
          </Button>
          <Button type="primary" :onclick="handleGridFull.bind(null)" style="margin-right: 20px">
            {{state.isFull?'退出全屏':'全屏展示'}}
          </Button>
        </header>
        <main class="el-main" style="padding: 0px;">
          <div :style="isFullStyle">
            <div v-for="i in state.spilt" :key="i" class="play-box" :style="liveStyle" @click="state.playerIdx = (i-1)" :class="{redborder:state.playerIdx == (i-1)}">>
              <div v-if="!state.playUrls[i-1]"
                   style="color: #ffffff;font-size: 30px;font-weight: bold;">{{ i }}
              </div>
              <Jessibuca ref="jessibuca" :play-url="state.playUrls[i-1]" :hasAudio="false"
                         v-else/>
            </div>
          </div>
        </main>
      </section>
      <div class="el-loading-mask" style="display: none;">
        <div class="el-loading-spinner">
          <svg viewBox="25 25 50 50" class="circular">
            <circle cx="50" cy="50" r="20" fill="none" class="path"></circle>
          </svg>
          <p class="el-loading-text">拼命加载中</p></div>
      </div>
    </section>
  </div>
</template>
<script lang="ts" setup>
import {computed, type CSSProperties, onMounted, reactive, ref} from 'vue'
import {BasicTree, type TreeItem} from "@/components/Tree";
import {handleTree} from "@/utils/tree";
import {getTree, playByDeviceAndChannel, queryVideoList, getDeviceChannels} from "@/api/device/gb28181";
import {Icon} from "@/components/Icon";
import {Button, TreeProps} from 'ant-design-vue';
import {useMessage} from "@/hooks/web/useMessage";
import Jessibuca from "@/components/Player/module/jessibuca.vue";

const {createMessage} = useMessage()

const selectedKeys = ref<string[]>([]);

const treeRef = ref()
const treeData = ref<TreeItem[]>([])
const state = reactive({
  subTree: false,
  playUrls: [] as any,
  isActive: [
    true, false, false, false
  ],
  spilt: 1,
  playerIdx: 0,
  isFull: false,
});

const isFullStyle = computed((): CSSProperties => {
  let style = {width: '93%', height: '77vh', display: 'flex', flexWrap: 'wrap', backgroundColor: 'rgb(0, 0, 0)'}
  if(state.isFull) {
    style = {width: '100%', height: '100vh', display: 'flex', flexWrap: 'wrap', backgroundColor: 'rgb(0, 0, 0)'}
  }
  console.log(style);
  return style;
})

const liveStyle = computed((): CSSProperties => {
  let style = {width: '100%', height: '100%'}
  switch (state.spilt) {
    case 4:
      style = {width: '50%', height: '50%'}
      break
    case 9:
      style = {width: '33.3%', height: '33.3%'}
      break
    case 16:
      style = {width: '25%', height: '25%'}
      break
  }
  return style;
})

async function handleSelect(keys) {
  if ((keys + '') == '') {
    createMessage.warn('请选择一个摄像头');
    return;
  }
  if ((keys + '').indexOf(',') == -1) {
    createMessage.warn('无效摄像头');
    return;
  }
  const tmp = (keys + '').split(',');
  console.log(tmp)
  playByDeviceAndChannel(tmp[0], tmp[1]).then((data) => {
    if (data && data.data) {
      state.playUrls[state.playerIdx] = data.data.ws_flv || data.data.https_flv || data.data.rtmp;
    }
  }).catch((error) => {
    console.error('播放失败:', error);
    createMessage.error('播放失败');
  });
}

async function handleGridChange(num) {
  for (let i = 0; i < state.isActive.length; i++) {
    state.isActive[i] = false;
  }
  state.playUrls.splice(state.spilt, state.playUrls.length);
  console.log(state.playUrls);
  state.isActive[num] = true;
  state.spilt = (num + 1) * (num + 1);
}

async function handleGridDelete() {
  console.log(state.playerIdx);
  state.playUrls.splice(state.playerIdx, 1)
}

async function handleGridFull() {
  state.isFull = !state.isFull;
}

async function fetchTree() {
  const res = await queryVideoList({
    pageNum: 1,
    pageSize: 10000,
  })
  let tree = handleTree(res['data'], 'deviceIdentification')
  for (let i = 0; i < tree.length; i++) {
    tree[i]['deviceId'] = tree[i]['deviceIdentification']
  }
  treeData.value = tree;
}

const onLoadData: TreeProps['loadData'] = treeNode => {
  let tmpArr = [];
  let tmpIndex = [];
  let tmpLoop = [];
  return new Promise(resolve => {
    if (treeNode.dataRef.children) {
      resolve();
      return;
    }
    setTimeout(() => {
      treeNode.isLeaf = true;
      getDeviceChannels(treeNode.dataRef.deviceIdentification).then((res) => {
        tmpArr = treeNode['pos'].split('-');
        tmpIndex = tmpArr[tmpArr.length - 1];
        // 处理通道列表数据
        const channels = res.data || res.list || [];
        tmpLoop = handleTree(channels, 'deviceId');
        for (let i = 0; i < tmpLoop.length; i++) {
          const channel = tmpLoop[i];
          const deviceId = channel.deviceId || channel.deviceIdentification || treeNode.dataRef.deviceIdentification;
          const channelId = channel.channelId || channel.deviceChannelId || channel.id;
          tmpLoop[i]['deviceId'] = deviceId + "," + channelId;
        }
        treeData.value[tmpIndex]['children'] = tmpLoop;
        console.log(treeData.value)
        resolve();
      }).catch((error) => {
        console.error('加载通道列表失败:', error);
        createMessage.error('加载通道列表失败');
        resolve();
      })
    }, 1000);
  });
};

onMounted(() => {
  fetchTree();
})
</script>

<style>
#DeviceTree {
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

    .el-header, .el-footer {
      /* background-color: #b3c0d1; */
      color: #333;
      text-align: center;
      line-height: 60px;
    }

    .el-header {
      padding: 0 20px;
      -webkit-box-sizing: border-box;
      box-sizing: border-box;
      -ms-flex-negative: 0;
      flex-shrink: 0;
    }

    .el-main {
      background-color: #f0f2f5;
      color: #333;
      text-align: center;
      padding-top: 0px !important;

      .device-tree-main-box {
        text-align: left;

        .el-tree {
          position: relative;
          cursor: default;
          background: #FFF;
          color: #606266;

          .el-tree-node {
            white-space: nowrap;
            outline: 0;

            .el-tree-node__content {
              display: -webkit-box;
              display: -ms-flexbox;
              display: flex;
              -webkit-box-align: center;
              -ms-flex-align: center;
              align-items: center;
              height: 26px;
              cursor: pointer;

              .custom-tree-node {
                .el-tree-node__content {
                  display: -webkit-box;
                  display: -ms-flexbox;
                  display: flex;
                  -webkit-box-align: center;
                  -ms-flex-align: center;
                  align-items: center;
                  height: 26px;
                  cursor: pointer;

                  .device-offline {
                    color: #727272;
                  }
                }
              }

              & > .el-tree-node__expand-icon {
                padding: 6px;
              }

              .el-tree-node__expand-icon {
                cursor: pointer;
                color: #C0C4CC;
                font-size: 0.75rem;
                -webkit-transform: rotate(0);
                transform: rotate(0);
                -webkit-transition: -webkit-transform .3s ease-in-out;
                transition: -webkit-transform .3s ease-in-out;
                transition: transform .3s ease-in-out;
                transition: transform .3s ease-in-out, -webkit-transform .3s ease-in-out;
                transition: transform .3s ease-in-out, -webkit-transform .3s ease-in-out;
              }
            }
          }
        }
      }
    }

    .el-main {
      display: block;
      -webkit-box-flex: 1;
      -ms-flex: 1;
      flex: 1;
      -ms-flex-preferred-size: auto;
      flex-basis: auto;
      overflow: auto;
      -webkit-box-sizing: border-box;
      box-sizing: border-box;
    }
  }

  .el-container.is-vertical {
    -ms-flex-direction: column;
    -webkit-box-orient: vertical;
    -webkit-box-direction: normal;
    flex-direction: column;
  }
}

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

    .el-container.full {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 99999;
      width: 100%;
    }

    .el-aside {
      overflow: auto;
      -webkit-box-sizing: border-box;
      box-sizing: border-box;
      -ms-flex-negative: 0;
      flex-shrink: 0;
    }

    .el-container.is-vertical {
      -ms-flex-direction: column;
      -webkit-box-orient: vertical;
      -webkit-box-direction: normal;
      flex-direction: column;
    }

    .el-container.is-vertical, .el-drawer, .el-empty, .el-result {
      -webkit-box-orient: vertical;
      -webkit-box-direction: normal;
    }

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

      .el-header, .el-footer {
        /* background-color: #b3c0d1; */
        color: #333;
        text-align: center;
        line-height: 60px;

        & > span {
          cursor: pointer;
          width: 25px;
          height: 25px;
          margin: 0 15px;
        }

        & > span.active {
          color: #409EFF;
        }
      }

      .el-header {
        padding: 0 20px;
        -webkit-box-sizing: border-box;
        box-sizing: border-box;
        -ms-flex-negative: 0;
        flex-shrink: 0;

        .btn.active {
          color: #409EFF;
        }

        .btn {
          margin: 0 10px;
        }
      }

      .el-main {
        background-color: #f0f2f5;
        color: #333;
        text-align: center;
        padding-top: 0px !important;
      }

      .el-main {
        display: block;
        -webkit-box-flex: 1;
        -ms-flex: 1;
        flex: 1;
        -ms-flex-preferred-size: auto;
        flex-basis: auto;
        overflow: auto;
        -webkit-box-sizing: border-box;
        box-sizing: border-box;

        .play-box {
          background-color: #000000;
          border: 0.5px solid #505050;
          display: -webkit-box;
          display: -ms-flexbox;
          display: flex;
          -webkit-box-align: center;
          -ms-flex-align: center;
          align-items: center;
          -webkit-box-pack: center;
          -ms-flex-pack: center;
          justify-content: center;

          .jessibuca-container {
            position: relative;
            display: block;
            width: 100%;
            height: 100%;
            overflow: hidden;
          }
        }

        .redborder {
          border: 2px solid red !important;
        }
      }
    }

    &.is-vertical {
      -ms-flex-direction: column;
      -webkit-box-orient: vertical;
      -webkit-box-direction: normal;
      flex-direction: column;
    }

    .el-loading-mask {
      position: absolute;
      z-index: 2000;
      background-color: rgba(255, 255, 255, .9);
      margin: 0;
      top: 0;
      right: 0;
      bottom: 0;
      left: 0;
      -webkit-transition: opacity .3s;
      transition: opacity .3s;
    }
  }
}
</style>
