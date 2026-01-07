<template>
  <div :class="['split-screen-container', { 'fullscreen-mode': state.isFull }]">
    <a-layout class="monitor-layout">
      <!-- 左侧设备树 -->
      <a-layout-sider
        :width="320"
        class="device-tree-sider"
        :theme="'light'"
      >
        <CollapseContainer
          :can-expan="true"
          :title="'设备列表'"
          class="tree-container"
        >
          <template #title>
            <div class="tree-header">
              <Icon icon="ant-design:apartment-outlined" class="header-icon" />
              <span class="header-title">设备列表</span>
            </div>
          </template>
          <ScrollContainer class="tree-scroll">
            <BasicTree
              ref="treeRef"
              search
              :showIcon="true"
              v-model:selectedKeys="selectedKeys"
              @select="handleSelect"
              :tree-data="treeData"
              :load-data="onLoadData"
              :field-names="{ key: 'deviceId', title: 'name' }"
              class="device-tree"
            />
          </ScrollContainer>
        </CollapseContainer>
      </a-layout-sider>

      <!-- 右侧监控区域 -->
      <a-layout class="monitor-content-layout">
        <!-- 工具栏 -->
        <a-layout-header class="toolbar-header">
          <div class="toolbar-content">
            <!-- 分屏模式选择 -->
            <div class="toolbar-section">
              <a-radio-group
                v-model:value="state.splitMode"
                size="middle"
                button-style="solid"
                class="split-mode-group"
                @change="handleSplitModeChange"
              >
                <a-radio-button :value="1">
                  <Icon icon="akar-icons:full-screen" class="radio-icon" />
                  <span>1分屏</span>
                </a-radio-button>
                <a-radio-button :value="4">
                  <Icon icon="ic:sharp-grid-view" class="radio-icon" />
                  <span>4分屏</span>
                </a-radio-button>
                <a-radio-button :value="9">
                  <Icon icon="bi:grid-3x3-gap-fill" class="radio-icon" />
                  <span>9分屏</span>
                </a-radio-button>
                <a-radio-button :value="16">
                  <Icon icon="material-symbols:background-grid-small" class="radio-icon" />
                  <span>16分屏</span>
                </a-radio-button>
              </a-radio-group>
            </div>

            <a-divider type="vertical" class="toolbar-divider" />

            <!-- 操作按钮 -->
            <div class="toolbar-section">
              <div class="section-label">
                <Icon icon="ant-design:tool-outlined" class="label-icon" />
                <span>操作</span>
              </div>
              <a-space size="small" class="action-buttons">
                <a-button
                  type="default"
                  danger
                  size="middle"
                  @click="handleGridDelete"
                  :disabled="!state.playUrls[state.playerIdx]"
                  class="action-btn"
                >
                  <template #icon>
                    <Icon icon="ant-design:delete-outlined" />
                  </template>
                  删除选中
                </a-button>
                <a-button
                  :type="state.isFull ? 'default' : 'primary'"
                  size="middle"
                  @click="handleGridFull"
                  class="action-btn"
                >
                  <template #icon>
                    <Icon :icon="state.isFull ? 'ant-design:fullscreen-exit-outlined' : 'ant-design:fullscreen-outlined'" />
                  </template>
                  {{ state.isFull ? '退出全屏' : '全屏展示' }}
                </a-button>
                <a-button
                  type="default"
                  size="middle"
                  @click="handleClearAll"
                  class="action-btn"
                >
                  <template #icon>
                    <Icon icon="ant-design:clear-outlined" />
                  </template>
                  清空全部
                </a-button>
              </a-space>
            </div>

            <!-- 状态信息 -->
            <div class="toolbar-section toolbar-status">
              <a-badge :status="state.isFull ? 'processing' : 'default'" :text="state.isFull ? '全屏模式' : '窗口模式'" />
              <span class="status-text">已加载: {{ loadedCount }}/{{ state.splitMode }}</span>
            </div>
          </div>
        </a-layout-header>

        <!-- 视频播放区域 -->
        <a-layout-content class="video-content">
          <div :class="['video-grid', `grid-${state.splitMode}`]" :style="gridStyle">
            <div
              v-for="i in state.splitMode"
              :key="i"
              :class="['video-cell', { 
                'cell-selected': state.playerIdx === i - 1, 
                'cell-empty': !state.playUrls[i - 1],
                'cell-loading': state.loadingCells.includes(i - 1)
              }]"
              @click="state.playerIdx = i - 1"
            >
              <div v-if="!state.playUrls[i - 1]" class="empty-cell">
                <div class="empty-icon-wrapper">
                  <Icon icon="ant-design:video-camera-add-outlined" class="empty-icon" />
                </div>
                <span class="empty-text">通道 {{ i }}</span>
                <span class="empty-hint">点击左侧设备树选择通道</span>
              </div>
              <div v-else class="player-wrapper">
                <Jessibuca
                  :ref="(el) => setPlayerRef(el, i - 1)"
                  :play-url="state.playUrls[i - 1]"
                  :hasAudio="false"
                />
                <div class="cell-overlay">
                  <a-tag color="processing" class="cell-tag">
                    <Icon icon="ant-design:video-camera-outlined" class="tag-icon" />
                    通道 {{ i }}
                  </a-tag>
                  <div class="cell-actions">
                    <a-button
                      type="text"
                      size="small"
                      danger
                      class="cell-action-btn"
                      @click.stop="handleCellDelete(i - 1)"
                    >
                      <Icon icon="ant-design:close-outlined" />
                    </a-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </a-layout-content>
      </a-layout>
    </a-layout>
  </div>
</template>

<script lang="ts" setup>
import { computed, type CSSProperties, onMounted, onUnmounted, reactive, ref } from 'vue';
import { 
  Layout as ALayout, 
  LayoutSider as ALayoutSider, 
  LayoutHeader as ALayoutHeader, 
  LayoutContent as ALayoutContent, 
  Space as ASpace, 
  Button as AButton, 
  Divider as ADivider, 
  Tag as ATag,
  RadioGroup as ARadioGroup,
  RadioButton as ARadioButton,
  Badge as ABadge
} from 'ant-design-vue';
import { BasicTree, type TreeItem } from '@/components/Tree';
import { Icon } from '@/components/Icon';
import { CollapseContainer } from '@/components/Container';
import { ScrollContainer } from '@/components/Container';
import { handleTree } from '@/utils/tree';
import { playByDeviceAndChannel, queryVideoList, getDeviceChannels } from '@/api/device/gb28181';
import type { TreeProps } from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import Jessibuca from '@/components/Player/module/jessibuca.vue';

const { createMessage } = useMessage();

const selectedKeys = ref<string[]>([]);
const treeRef = ref();
const treeData = ref<TreeItem[]>([]);
const playerRefs = ref<any[]>([]);

const state = reactive({
  siderCollapsed: false,
  playUrls: [] as any[],
  splitMode: 1,
  playerIdx: 0,
  isFull: false,
  loadingCells: [] as number[],
});

const loadedCount = computed(() => {
  return state.playUrls.filter(url => url).length;
});

const gridStyle = computed((): CSSProperties => {
  const baseStyle: CSSProperties = {
    display: 'grid',
    gridTemplateColumns: `repeat(${Math.sqrt(state.splitMode)}, 1fr)`,
    gridTemplateRows: `repeat(${Math.sqrt(state.splitMode)}, 1fr)`,
    gap: '2px',
    backgroundColor: '#ffffff',
    width: '100%',
    height: '100%',
    padding: '2px',
  };

  if (state.isFull) {
    return {
      ...baseStyle,
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      zIndex: 9999,
    };
  }

  return baseStyle;
});

const setPlayerRef = (el: any, index: number) => {
  if (el) {
    playerRefs.value[index] = el;
  }
};

async function handleSelect(keys: any) {
  const keyStr = String(keys);
  if (!keyStr) {
    createMessage.warn('请选择一个摄像头');
    return;
  }
  if (keyStr.indexOf(',') === -1) {
    createMessage.warn('无效摄像头');
    return;
  }
  const [deviceId, channelId] = keyStr.split(',');
  
  // 检查当前选中的格子是否已有视频
  if (state.playUrls[state.playerIdx]) {
    createMessage.warn('当前通道已有视频，请先删除或选择其他通道');
    return;
  }

  // 添加加载状态
  if (!state.loadingCells.includes(state.playerIdx)) {
    state.loadingCells.push(state.playerIdx);
  }

  try {
    const data = await playByDeviceAndChannel(deviceId, channelId);
    if (data?.data) {
      state.playUrls[state.playerIdx] = data.data.ws_flv || data.data.https_flv || data.data.rtmp;
      createMessage.success('视频加载成功');
    }
  } catch (error) {
    console.error('播放失败:', error);
    createMessage.error('播放失败，请检查设备连接');
  } finally {
    // 移除加载状态
    const index = state.loadingCells.indexOf(state.playerIdx);
    if (index > -1) {
      state.loadingCells.splice(index, 1);
    }
  }
}

function handleSplitModeChange() {
  const newSplit = state.splitMode;
  
  // 清理超出当前分屏数量的播放地址
  if (state.playUrls.length > newSplit) {
    state.playUrls = state.playUrls.slice(0, newSplit);
  } else {
    // 扩展数组到新长度
    while (state.playUrls.length < newSplit) {
      state.playUrls.push(null);
    }
  }
  
  // 确保选中索引不超出范围
  if (state.playerIdx >= newSplit) {
    state.playerIdx = 0;
  }
}

function handleGridDelete() {
  if (state.playUrls[state.playerIdx]) {
    // 停止播放
    if (playerRefs.value[state.playerIdx]) {
      playerRefs.value[state.playerIdx].destroy?.();
    }
    state.playUrls[state.playerIdx] = null;
    createMessage.success('已删除选中通道');
    // 如果删除后当前索引超出范围，重置为0
    if (state.playerIdx >= state.playUrls.length) {
      state.playerIdx = Math.max(0, state.playUrls.length - 1);
    }
  } else {
    createMessage.warn('当前通道没有视频');
  }
}

function handleCellDelete(index: number) {
  if (state.playUrls[index]) {
    // 停止播放
    if (playerRefs.value[index]) {
      playerRefs.value[index].destroy?.();
    }
    state.playUrls[index] = null;
    createMessage.success('已删除通道');
  }
}

function handleClearAll() {
  // 停止所有播放
  playerRefs.value.forEach((player, index) => {
    if (player && state.playUrls[index]) {
      player.destroy?.();
    }
  });
  state.playUrls = new Array(state.splitMode).fill(null);
  state.playerIdx = 0;
  createMessage.success('已清空所有通道');
}

function handleGridFull() {
  state.isFull = !state.isFull;
  if (state.isFull) {
    document.documentElement.requestFullscreen?.();
  } else {
    document.exitFullscreen?.();
  }
}

async function fetchTree() {
  try {
    const res = await queryVideoList({
      pageNum: 1,
      pageSize: 10000,
    });
    let tree = handleTree(res.data, 'deviceIdentification');
    for (let i = 0; i < tree.length; i++) {
      tree[i].deviceId = tree[i].deviceIdentification;
    }
    treeData.value = tree;
  } catch (error) {
    console.error('加载设备树失败:', error);
    createMessage.error('加载设备树失败');
  }
}

const onLoadData: TreeProps['loadData'] = (treeNode) => {
  return new Promise((resolve) => {
    if (treeNode.dataRef.children) {
      resolve();
      return;
    }
    
    setTimeout(() => {
      treeNode.isLeaf = true;
      getDeviceChannels(treeNode.dataRef.deviceIdentification)
        .then((res) => {
          const tmpArr = treeNode.pos.split('-');
          const tmpIndex = parseInt(tmpArr[tmpArr.length - 1]);
          
          // 处理通道列表数据
          const channels = res.data || res.list || [];
          const tmpLoop = handleTree(channels, 'deviceId');
          
          for (let i = 0; i < tmpLoop.length; i++) {
            const channel = tmpLoop[i];
            const deviceId = channel.deviceId || channel.deviceIdentification || treeNode.dataRef.deviceIdentification;
            const channelId = channel.channelId || channel.deviceChannelId || channel.id;
            tmpLoop[i].deviceId = `${deviceId},${channelId}`;
          }
          
          treeData.value[tmpIndex].children = tmpLoop;
          resolve();
        })
        .catch((error) => {
          console.error('加载通道列表失败:', error);
          createMessage.error('加载通道列表失败');
          resolve();
        });
    }, 300);
  });
};

// 监听全屏变化
const handleFullscreenChange = () => {
  state.isFull = !!document.fullscreenElement;
};

// 初始化播放地址数组
onMounted(() => {
  fetchTree();
  // 初始化播放地址数组
  state.playUrls = Array(state.splitMode).fill(null);
  
  // 监听全屏变化
  document.addEventListener('fullscreenchange', handleFullscreenChange);
});

// 清理事件监听器
onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange);
  // 清理所有播放器
  playerRefs.value.forEach((player) => {
    if (player && player.destroy) {
      player.destroy();
    }
  });
});
</script>

<style lang="less" scoped>
.split-screen-container {
  height: 100%;
  min-height: calc(100vh - 200px);
  background: #ffffff;
  position: relative;

  &.fullscreen-mode {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 9999;
    background: #ffffff;
    min-height: 100vh;
  }

  .monitor-layout {
    height: 100%;
    min-height: 100%;
    background: transparent;

    .device-tree-sider {
      background: #ffffff;
      border-right: 1px solid #e5e7eb;
      box-shadow: 2px 0 12px rgba(0, 0, 0, 0.05);

      :deep(.ant-layout-sider-children) {
        display: flex;
        flex-direction: column;
        height: 100%;
      }

      .tree-container {
        height: 100%;
        display: flex;
        flex-direction: column;
        background: transparent;

        :deep(.ant-collapse) {
          background: transparent;
          border: none;
        }

        :deep(.ant-collapse-header) {
          background: #ffffff;
          border-bottom: 1px solid #e5e7eb;
          padding: 16px 20px;
          color: #1f2937;
          font-weight: 600;
          font-size: 15px;
        }

        .tree-header {
          display: flex;
          align-items: center;
          gap: 10px;
          color: #1f2937;

          .header-icon {
            font-size: 18px;
            color: #3b82f6;
          }

          .header-title {
            font-weight: 600;
            font-size: 15px;
          }
        }

        .tree-scroll {
          flex: 1;
          overflow: hidden;
          padding: 12px;
          background: #ffffff;

          .device-tree {
            :deep(.ant-tree) {
              background: transparent;
              color: #1f2937;

              .ant-tree-node-selected {
                background: rgba(59, 130, 246, 0.15) !important;
              }

              .ant-tree-switcher {
                color: #6b7280;
              }
            }

            :deep(.ant-input-search) {
              .ant-input {
                background: #ffffff;
                border-color: #d1d5db;
                color: #1f2937;

                &::placeholder {
                  color: #9ca3af;
                }

                &:focus {
                  border-color: #3b82f6;
                  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
                }
              }
            }
          }
        }
      }
    }

    .monitor-content-layout {
      display: flex;
      flex-direction: column;
      height: 100%;
      min-height: 100%;
      background: #ffffff;

      .toolbar-header {
        height: 88px;
        padding: 0 24px;
        background: #ffffff;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);

        .toolbar-content {
          width: 100%;
          display: flex;
          align-items: center;
          gap: 24px;
          flex-wrap: wrap;

          .toolbar-section {
            display: flex;
            align-items: center;
            gap: 12px;

            .section-label {
              display: inline-flex;
              align-items: center;
              gap: 6px;
              font-weight: 500;
              color: #374151;
              font-size: 14px;
              white-space: nowrap;

              .label-icon {
                font-size: 16px;
                color: #3b82f6;
              }
            }

            .split-mode-group {
              :deep(.ant-radio-button-wrapper) {
                background: #ffffff;
                border-color: #d1d5db;
                color: #374151;
                transition: all 0.3s;

                &.ant-radio-button-wrapper-checked {
                  background: #3b82f6;
                  border-color: #3b82f6;
                  color: #fff;
                  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
                }

                .radio-icon {
                  margin-right: 4px;
                }
              }
            }

            .action-buttons {
              .action-btn {
                transition: all 0.3s;
              }
            }
          }

          .toolbar-divider {
            height: 40px;
            border-color: #e5e7eb;
          }

          .toolbar-status {
            margin-left: auto;
            display: flex;
            align-items: center;
            gap: 16px;

            .status-text {
              color: #6b7280;
              font-size: 13px;
            }
          }
        }
      }

      .video-content {
        flex: 1;
        min-height: 0;
        overflow: hidden;
        background: #ffffff;
        position: relative;

        .video-grid {
          width: 100%;
          height: 100%;

          .video-cell {
            position: relative;
            border: 2px solid #e5e7eb;
            box-sizing: border-box;
            background: #f9fafb;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
            overflow: hidden;
            border-radius: 2px;
            width: 100%;
            height: 100%;
            min-height: 100%;


            &.cell-selected {
              border-color: #3b82f6;
              box-shadow: 0 0 24px rgba(59, 130, 246, 0.6);
              z-index: 20;
            }

            &.cell-loading {
              &::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255, 255, 255, 0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 5;
              }
            }

            &.cell-empty {
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              background: #ffffff;
              border-style: dashed;
              width: 100%;
              height: 100%;
              min-height: 100%;

              .empty-cell {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 16px;
                color: #6b7280;
                width: 100%;
                height: 100%;

                .empty-icon-wrapper {
                  width: 64px;
                  height: 64px;
                  border-radius: 50%;
                  background: rgba(59, 130, 246, 0.1);
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  border: 2px dashed rgba(59, 130, 246, 0.3);
                }

                .empty-icon {
                  font-size: 32px;
                  color: #3b82f6;
                }

                .empty-text {
                  font-size: 16px;
                  font-weight: 600;
                  color: #374151;
                }

                .empty-hint {
                  font-size: 12px;
                  color: #6b7280;
                }
              }
            }

            .player-wrapper {
              width: 100%;
              height: 100%;
              position: relative;

              :deep(.jessibuca-container) {
                width: 100%;
                height: 100%;
              }

              .cell-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                padding: 8px 12px;
                z-index: 30;
                pointer-events: none;
                background: linear-gradient(180deg, rgba(0, 0, 0, 0.6) 0%, transparent 100%);
                display: flex;
                justify-content: space-between;
                align-items: center;
                opacity: 0;
                transition: opacity 0.3s;
              }

              .cell-tag {
                margin: 0;
                font-weight: 500;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                background: rgba(59, 130, 246, 0.9);
                border: none;
                display: inline-flex;
                align-items: center;
                gap: 4px;

                .tag-icon {
                  font-size: 12px;
                }
              }

              .cell-actions {
                pointer-events: all;

                .cell-action-btn {
                  color: #fff;
                  background: rgba(239, 68, 68, 0.8);
                  border-radius: 4px;
                  padding: 4px 8px;

                  &:hover {
                    background: rgba(239, 68, 68, 1);
                    color: #fff;
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

:deep(.ant-layout-sider) {
  overflow: hidden;
}

:deep(.ant-layout-content) {
  overflow: hidden;
}
</style>
