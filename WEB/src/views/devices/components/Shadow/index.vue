<template>
  <div class="shadow-container">
    <!-- 左侧筛选/信息面板 -->
    <div class="info-panel">
      <div class="info-header">
        <h3>设备影子</h3>
      </div>
      <div class="info-content">
        <div class="info-item">
          <div class="info-label">设备标识</div>
          <div class="info-value">{{ deviceId || '--' }}</div>
        </div>
        <div class="info-item">
          <div class="info-label">更新时间</div>
          <div class="info-value">{{ lastUpdateTime || '--' }}</div>
        </div>
        <div class="info-item">
          <div class="info-label">版本号</div>
          <div class="info-value">{{ shadowVersion || '--' }}</div>
        </div>
        <div class="info-actions">
          <Button type="primary" @click="refreshShadow" :loading="loading" block>
            <Icon icon="ant-design:reload-outlined" />
            刷新数据
          </Button>
        </div>
      </div>
    </div>

    <!-- 右侧 JSON 展示 -->
    <div class="json-panel">
      <div class="json-header">
        <div class="json-title">
          <Icon icon="ant-design:code-outlined" />
          <span>影子数据 (JSON)</span>
        </div>
        <div class="json-actions">
          <Button size="small" @click="copyJson" :disabled="!shadowData">
            <Icon icon="ant-design:copy-outlined" />
            复制
          </Button>
          <Button size="small" @click="formatJson" :disabled="!shadowData">
            <Icon icon="ant-design:format-painter-outlined" />
            格式化
          </Button>
        </div>
      </div>
      <div class="json-content" ref="jsonContainerRef">
        <div v-if="!shadowData" class="empty-state">
          <Icon icon="ant-design:inbox-outlined" />
          <p>暂无影子数据</p>
        </div>
        <pre v-else class="json-display" :class="{ 'formatted': isFormatted }">{{ displayJson }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { defHttp } from '@/utils/http/axios';
import moment from 'moment';
import { Button } from 'ant-design-vue';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';

defineOptions({ name: 'DeviceShadow' });

const route = useRoute();
const { createMessage } = useMessage();

// 获取设备ID
const deviceId = computed(() => route.params?.id as string);

// 影子数据
const shadowData = ref<any>(null);
const shadowVersion = ref<string>('');
const lastUpdateTime = ref<string>('');
const loading = ref(false);
const isFormatted = ref(true);
const jsonContainerRef = ref<HTMLElement | null>(null);

// 显示的 JSON
const displayJson = computed(() => {
  if (!shadowData.value) return '';
  
  try {
    if (isFormatted.value) {
      return JSON.stringify(shadowData.value, null, 2);
    } else {
      return JSON.stringify(shadowData.value);
    }
  } catch (error) {
    return String(shadowData.value);
  }
});

// 获取设备影子数据
const fetchShadowData = async () => {
  loading.value = true;
  try {
    defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
    
    const response = await defHttp.get(
      {
        url: `/shadow/${deviceId.value}`,
      },
      { isTransformResponse: true },
    );
    
    // 处理返回数据格式
    let data = null;
    if (Array.isArray(response)) {
      // 如果是数组，转换为对象格式
      const obj: any = {};
      response.forEach((item: any) => {
        if (item.key && item.value !== undefined) {
          obj[item.key] = item.value;
        }
      });
      data = obj;
      
      // 从数组中提取版本和时间信息
      if (response.length > 0) {
        const firstItem = response[0];
        shadowVersion.value = firstItem.version || '';
        lastUpdateTime.value = firstItem.updateTime 
          ? moment(firstItem.updateTime).format('YYYY-MM-DD HH:mm:ss')
          : '';
      }
    } else if (typeof response === 'object' && response !== null) {
      data = response;
      
      // 提取版本和时间信息
      if (response.version) {
        shadowVersion.value = response.version;
      }
      if (response.updateTime) {
        lastUpdateTime.value = moment(response.updateTime).format('YYYY-MM-DD HH:mm:ss');
      } else if (response.timestamp) {
        lastUpdateTime.value = moment(response.timestamp).format('YYYY-MM-DD HH:mm:ss');
      }
    }
    
    shadowData.value = data;
    
    if (!shadowData.value || Object.keys(shadowData.value).length === 0) {
      createMessage.warning('设备影子数据为空');
    }
  } catch (error) {
    console.error('获取设备影子数据失败:', error);
    createMessage.error('获取设备影子失败');
    shadowData.value = null;
  } finally {
    loading.value = false;
  }
};

// 刷新影子数据
const refreshShadow = () => {
  fetchShadowData();
};

// 复制 JSON
const copyJson = async () => {
  if (!displayJson.value) return;
  
  try {
    await navigator.clipboard.writeText(displayJson.value);
    createMessage.success('已复制到剪贴板');
  } catch (error) {
    // 降级方案
    const textArea = document.createElement('textarea');
    textArea.value = displayJson.value;
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      createMessage.success('已复制到剪贴板');
    } catch (err) {
      createMessage.error('复制失败');
    }
    document.body.removeChild(textArea);
  }
};

// 格式化 JSON
const formatJson = () => {
  isFormatted.value = !isFormatted.value;
  createMessage.success(isFormatted.value ? '已格式化' : '已压缩');
};

onMounted(() => {
  fetchShadowData();
});
</script>

<style lang="less" scoped>
.shadow-container {
  display: flex;
  height: 100%;
  min-height: 500px;
  gap: 12px;
  background: transparent;

  // 左侧信息面板
  .info-panel {
    width: 300px;
    flex-shrink: 0;
    background: #ffffff;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    border: 1px solid #f0f0f0;
    display: flex;
    flex-direction: column;
    align-self: flex-start;
    height: fit-content;
    max-height: calc(100vh - 200px);

    .info-header {
      padding: 14px 18px;
      border-bottom: 1px solid #f5f5f5;
      background: linear-gradient(to bottom, #fafafa, #ffffff);

      h3 {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
        color: #262626;
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }

    .info-content {
      padding: 18px;
      overflow-y: auto;

      .info-item {
        margin-bottom: 18px;
        padding-bottom: 18px;
        border-bottom: 1px solid #f5f5f5;

        &:last-of-type {
          border-bottom: none;
          margin-bottom: 0;
        }

        .info-label {
          font-size: 12px;
          font-weight: 500;
          color: #8c8c8c;
          margin-bottom: 8px;
        }

        .info-value {
          font-size: 13px;
          font-weight: 500;
          color: #262626;
          word-break: break-all;
          line-height: 1.6;
        }
      }

      .info-actions {
        margin-top: 20px;

        :deep(.ant-btn) {
          border-radius: 6px;
          height: 38px;
          font-weight: 500;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          box-shadow: 0 2px 4px rgba(24, 144, 255, 0.1);
          transition: all 0.3s ease;

          &:hover {
            box-shadow: 0 4px 8px rgba(24, 144, 255, 0.15);
            transform: translateY(-1px);
          }
        }
      }
    }
  }

  // 右侧 JSON 展示面板
  .json-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    border: 1px solid #f0f0f0;
    overflow: hidden;
    min-height: 0;

    .json-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      border-bottom: 1px solid #e8e8e8;
      background: #fafafa;
      flex-shrink: 0;

      .json-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        font-weight: 600;
        color: #262626;

        :deep(.anticon) {
          font-size: 16px;
          color: #1890ff;
        }
      }

      .json-actions {
        display: flex;
        gap: 8px;

        :deep(.ant-btn) {
          border-radius: 2px;
        }
      }
    }

    .json-content {
      flex: 1;
      overflow-y: auto;
      overflow-x: auto;
      padding: 16px;
      background: #1e1e1e;
      position: relative;
      min-height: 0;

      &::-webkit-scrollbar {
        width: 8px;
        height: 8px;
      }

      &::-webkit-scrollbar-track {
        background: #2d2d2d;
      }

      &::-webkit-scrollbar-thumb {
        background: #555;
        border-radius: 0;

        &:hover {
          background: #666;
        }
      }

      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        min-height: 300px;
        color: #999;

        :deep(.anticon) {
          font-size: 48px;
          margin-bottom: 16px;
          opacity: 0.5;
        }

        p {
          margin: 0;
          font-size: 14px;
        }
      }

      .json-display {
        margin: 0;
        padding: 0;
        font-size: 13px;
        line-height: 1.8;
        color: #d4d4d4;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
        white-space: pre;
        word-break: break-all;
        overflow-wrap: break-word;
        background: transparent;
        border: none;
        outline: none;
        user-select: text;
        cursor: text;

        &.formatted {
          white-space: pre-wrap;
        }

        // JSON 语法高亮（简单版本）
        :deep(.string) {
          color: #ce9178;
        }

        :deep(.number) {
          color: #b5cea8;
        }

        :deep(.boolean) {
          color: #569cd6;
        }

        :deep(.null) {
          color: #569cd6;
        }

        :deep(.key) {
          color: #9cdcfe;
        }
      }
    }
  }
}
</style>
