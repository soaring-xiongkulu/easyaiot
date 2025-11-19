<template>
  <div class="device-topic-wrapper">
    <div class="topic-container">
      <!-- 左侧导航栏 -->
      <div class="topic-sidebar">
        <Tabs
          v-model:activeKey="activeTab"
          tab-position="left"
          class="topic-tabs"
          @change="handleTabChange"
        >
          <TabPane
            v-for="tab in tabs"
            :key="tab.key"
            :tab="getTabTitle(tab)"
          >
          </TabPane>
        </Tabs>
      </div>

      <!-- 右侧内容区域 -->
      <div class="topic-main">
        <!-- 数据表格区域 -->
        <div class="topic-table-wrapper">
          <div v-if="filteredTopics.length > 0" class="topic-table">
            <!-- 表头 -->
            <div class="table-header">
              <div class="table-col col-topic">Topic</div>
              <div class="table-col col-type">类型</div>
              <div class="table-col col-desc">描述</div>
            </div>

            <!-- 表体 -->
            <div class="table-body">
              <div
                v-for="topic in paginatedTopics"
                :key="topic.id"
                class="table-row"
              >
                <div class="table-col col-topic">
                  <div class="cell-content">
                    <span class="topic-name-text" :title="topic.topicName">
                      {{ topic.topicName }}
                    </span>
                  </div>
                </div>
                <div class="table-col col-type">
                  <div class="cell-content">
                    <Tag :color="getTopicTypeColor(topic.topicType)" class="type-badge">
                      {{ getTopicTypeLabel(topic.topicType) }}
                    </Tag>
                  </div>
                </div>
                <div class="table-col col-desc">
                  <div class="cell-content">
                    <span class="desc-text" :title="topic.description">
                      {{ topic.description || '--' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-else class="topic-empty">
            <Empty description="暂无数据" />
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="filteredTopics.length > 0" class="topic-pagination">
          <Pagination
            v-model:current="pagination.current"
            v-model:pageSize="pagination.pageSize"
            :total="filteredTopics.length"
            :showSizeChanger="true"
            :showTotal="(total) => `共 ${total} 条记录`"
            :pageSizeOptions="['10', '20', '50', '100']"
            @change="handlePageChange"
            @showSizeChange="handlePageSizeChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { Tag, Empty, Pagination, Tabs, TabPane } from 'ant-design-vue';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons-vue';
import { getDevicesInfo } from '@/api/device/devices';
import moment from 'moment';

defineOptions({ name: 'DeviceTopic' });

const route = useRoute();

// 获取设备ID
const deviceId = computed(() => route.params?.id as string);

// Topic 枚举定义
interface TopicEnum {
  topicTemplate: string;
  needReply: boolean;
  description: string;
  category?: string;
}

const topicEnums: TopicEnum[] = [
  // 配置管理
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/config/downstream/push',
    needReply: true,
    description: '云端下行推送配置信息',
    category: '配置管理',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/config/downstream/query/ack',
    needReply: true,
    description: '云端下行回复配置查询',
    category: '配置管理',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/config/upstream/query',
    needReply: false,
    description: '设备上行查询配置信息',
    category: '配置管理',
  },
  // 设备标签管理
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/device/tag/downstream/report/ack',
    needReply: true,
    description: '云端下行回复标签上报',
    category: '设备标签管理',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/device/tag/upstream/delete',
    needReply: false,
    description: '设备上行删除标签信息',
    category: '设备标签管理',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/device/tag/upstream/report',
    needReply: false,
    description: '设备上行上报标签数据',
    category: '设备标签管理',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/device/tag/downstream/delete/ack',
    needReply: true,
    description: '云端下行回复标签删除',
    category: '设备标签管理',
  },
  // 设备影子
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/shadow/downstream/desired',
    needReply: true,
    description: '云端下行推送影子期望值变更',
    category: '设备影子',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/shadow/upstream/report',
    needReply: false,
    description: '设备上行上报影子状态',
    category: '设备影子',
  },
  // 时钟同步
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/ntp/downstream/response',
    needReply: true,
    description: '云端下行回复 NTP 时钟同步请求',
    category: '时钟同步',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/ntp/upstream/request',
    needReply: false,
    description: '设备上行请求 NTP 时钟同步',
    category: '时钟同步',
  },
  // 广播消息
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/broadcast/downstream/${identifier}',
    needReply: true,
    description: '云端下行广播消息，identifier 为用户自定义字符串',
    category: '广播消息',
  },
  // OTA 固件升级
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/ota/downstream/upgrade/task',
    needReply: true,
    description: '云端下行推送固件升级任务',
    category: 'OTA 固件升级',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/ota/upstream/version/report',
    needReply: false,
    description: '设备上行上报固件版本信息',
    category: 'OTA 固件升级',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/ota/upstream/progress/report',
    needReply: false,
    description: '设备上行上报固件升级进度',
    category: 'OTA 固件升级',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/ota/upstream/firmware/query',
    needReply: false,
    description: '设备上行查询固件信息',
    category: 'OTA 固件升级',
  },
  // 服务调用
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/service/downstream/invoke/${identifier}',
    needReply: true,
    description: '云端下行调用设备服务',
    category: '服务调用',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/service/upstream/invoke/${identifier}/response',
    needReply: false,
    description: '设备上行响应服务调用',
    category: '服务调用',
  },
  // 属性期望值设置
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/property/downstream/desired/set',
    needReply: true,
    description: '云端下行设置属性期望值',
    category: '属性期望值设置',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/property/upstream/desired/set/ack',
    needReply: false,
    description: '设备上行回复属性期望值设置',
    category: '属性期望值设置',
  },
  // 属性期望值获取
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/property/downstream/desired/query',
    needReply: true,
    description: '云端下行查询属性期望值',
    category: '属性期望值获取',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/property/upstream/desired/query/response',
    needReply: false,
    description: '设备上行回复属性期望值查询',
    category: '属性期望值获取',
  },
  // 属性上报
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/property/downstream/report/ack',
    needReply: true,
    description: '云端下行回复属性上报',
    category: '属性上报',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/property/upstream/report',
    needReply: false,
    description: '设备上行上报属性数据',
    category: '属性上报',
  },
  // 事件上报
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/event/downstream/report/${identifier}/ack',
    needReply: true,
    description: '云端下行回复事件上报',
    category: '事件上报',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/event/upstream/report/${identifier}',
    needReply: false,
    description: '设备上行上报事件数据',
    category: '事件上报',
  },
  // 日志上报
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/log/downstream/report/ack',
    needReply: true,
    description: '云端下行回复日志上报',
    category: '日志上报',
  },
  {
    topicTemplate: '/iot/${productIdentification}/${deviceIdentification}/log/upstream/report',
    needReply: false,
    description: '设备上行上报日志数据',
    category: '日志上报',
  },
];

// 设备信息
const deviceInfo = ref<{
  productIdentification?: string;
  deviceIdentification?: string;
}>({});

// Tab 配置
const tabs = [
  {
    key: 'upstream',
    label: '上行 Topic',
    icon: ArrowUpOutlined,
  },
  {
    key: 'downstream',
    label: '下行 Topic',
    icon: ArrowDownOutlined,
  },
];

// 当前激活的 Tab
const activeTab = ref('upstream');

// 所有 Topic 数据
const allTopics = ref<any[]>([]);

// 加载状态
const loading = ref(false);

// 搜索关键词
const searchKeyword = ref('');

// 分页配置
const pagination = ref({
  current: 1,
  pageSize: 10,
});

// 构建实际的 Topic
const buildTopic = (template: string, productIdentification: string, deviceIdentification: string, identifier?: string) => {
  let topic = template
    .replace('${productIdentification}', productIdentification)
    .replace('${deviceIdentification}', deviceIdentification);
  if (identifier) {
    topic = topic.replace('${identifier}', identifier);
  } else {
    // 如果没有 identifier，保留占位符显示
    topic = topic.replace('${identifier}', '*');
  }
  return topic;
};

// 获取设备信息并生成 Topic 数据
const fetchTopicData = async () => {
  loading.value = true;
  try {
    // 获取设备信息
    const deviceResponse = await getDevicesInfo(deviceId.value);
    const device = deviceResponse?.device || {};
    deviceInfo.value = {
      productIdentification: device.productIdentification || '',
      deviceIdentification: device.deviceIdentification || '',
    };

    // 根据枚举生成 Topic 列表
    const topics: any[] = [];
    topicEnums.forEach((topicEnum, index) => {
      const topicName = buildTopic(
        topicEnum.topicTemplate,
        deviceInfo.value.productIdentification || '',
        deviceInfo.value.deviceIdentification || ''
      );

      // needReply: true 表示下行（设备订阅 SUBSCRIBE），false 表示上行（设备发布 PUBLISH）
      const topicType = topicEnum.needReply ? 'SUBSCRIBE' : 'PUBLISH';

      topics.push({
        id: `topic-${index}`,
        topicName,
        topicType,
        permission: 'READ_WRITE', // 默认读写权限
        qos: 1, // 默认 QoS 1
        description: topicEnum.description,
        category: topicEnum.category,
        createTime: new Date().toISOString(),
      });
    });

    allTopics.value = topics;
  } catch (error) {
    console.error('获取Topic管理数据失败:', error);
    allTopics.value = [];
  } finally {
    loading.value = false;
  }
};

// 判断 Topic 类型
const isUpstreamTopic = (topicType: string) => {
  return topicType === 'PUBLISH' || topicType === 'PUB_SUB';
};

const isDownstreamTopic = (topicType: string) => {
  return topicType === 'SUBSCRIBE' || topicType === 'PUB_SUB';
};

// 获取当前 Tab 的 Topic 列表
const currentTabTopics = computed(() => {
  if (activeTab.value === 'upstream') {
    return allTopics.value.filter(topic => isUpstreamTopic(topic.topicType));
  } else {
    return allTopics.value.filter(topic => isDownstreamTopic(topic.topicType));
  }
});

// 过滤后的 Topic 列表
const filteredTopics = computed(() => {
  if (!searchKeyword.value) {
    return currentTabTopics.value;
  }
  const keyword = searchKeyword.value.toLowerCase();
  return currentTabTopics.value.filter(topic =>
    topic.topicName?.toLowerCase().includes(keyword)
  );
});

// 分页后的 Topic 列表
const paginatedTopics = computed(() => {
  const start = (pagination.value.current - 1) * pagination.value.pageSize;
  const end = start + pagination.value.pageSize;
  return filteredTopics.value.slice(start, end);
});

// 获取 Tab 数量
const getTabCount = (tabKey: string) => {
  if (tabKey === 'upstream') {
    return allTopics.value.filter(topic => isUpstreamTopic(topic.topicType)).length;
  } else {
    return allTopics.value.filter(topic => isDownstreamTopic(topic.topicType)).length;
  }
};

// 获取 Tab 标题
const getTabTitle = (tab: any) => {
  return `${tab.label} (${getTabCount(tab.key)})`;
};

// Tab 切换
const handleTabChange = (key: string) => {
  activeTab.value = key;
  pagination.value.current = 1;
  searchKeyword.value = '';
};

// 分页变化
const handlePageChange = (page: number) => {
  pagination.value.current = page;
};

const handlePageSizeChange = (current: number, size: number) => {
  pagination.value.current = 1;
  pagination.value.pageSize = size;
};

// 获取 Topic 类型标签
const getTopicTypeLabel = (topicType: string) => {
  const typeMap: Record<string, string> = {
    PUBLISH: '发布',
    SUBSCRIBE: '订阅',
    PUB_SUB: '发布订阅',
  };
  return typeMap[topicType] || topicType || '--';
};

// 获取 Topic 类型颜色
const getTopicTypeColor = (topicType: string) => {
  const colorMap: Record<string, string> = {
    PUBLISH: 'processing',
    SUBSCRIBE: 'success',
    PUB_SUB: 'warning',
  };
  return colorMap[topicType] || 'default';
};

// 获取权限标签
const getPermissionLabel = (permission: string) => {
  const permissionMap: Record<string, string> = {
    READ: '读',
    WRITE: '写',
    READ_WRITE: '读写',
  };
  return permissionMap[permission] || permission || '--';
};

// 获取权限颜色
const getPermissionColor = (permission: string) => {
  const colorMap: Record<string, string> = {
    READ: 'processing',
    WRITE: 'success',
    READ_WRITE: 'warning',
  };
  return colorMap[permission] || 'default';
};

// 格式化时间
const formatTime = (time: string) => {
  if (!time) return '--';
  return moment(time).format('YYYY-MM-DD HH:mm:ss');
};

// 初始化
onMounted(() => {
  fetchTopicData();
});
</script>

<style lang="less" scoped>
.device-topic-wrapper {
  padding: 0;
  margin: 0;
  background: #f5f7fa;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.topic-container {
  display: flex;
  height: 100%;
  width: 100%;
  background: #fff;
  overflow: hidden;
}

// 左侧导航栏
.topic-sidebar {
  width: 200px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.topic-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  :deep(.ant-tabs-nav) {
    margin: 0;
    padding: 0;
    background: #fff;
  }

  :deep(.ant-tabs-nav-list) {
    width: 100%;
    flex-direction: column;
  }

  :deep(.ant-tabs-tab) {
    width: 100%;
    margin: 0;
    padding: 0;
    border-radius: 0;
    text-align: left;
    transition: all 0.2s ease;
    border: none;
    border-bottom: 1px solid #e8e8e8;
    border-left: 3px solid transparent;
    background: #fff;

    &:hover {
      background: #fafafa;
    }

    &:last-child {
      border-bottom: none;
    }
  }

  :deep(.ant-tabs-tab-active) {
    background: #f0f5ff;
    border-left-color: #1890ff;
    border-bottom-color: #e8e8e8;

    .ant-tabs-tab-btn {
      color: #1890ff;
      font-weight: 600;
    }

    &:hover {
      background: #f0f5ff;
    }
  }

  :deep(.ant-tabs-tab-btn) {
    width: 100%;
    padding: 14px 16px;
    color: #595959;
    font-size: 14px;
    transition: color 0.2s ease;
    text-align: left;
  }

  :deep(.ant-tabs-ink-bar) {
    display: none;
  }

  :deep(.ant-tabs-content-holder) {
    display: none;
  }
}

// 右侧主内容区
.topic-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #fff;
  padding: 0;
  margin: 0;
}

// 表格区域
.topic-table-wrapper {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.topic-table {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

// 表头
.table-header {
  display: grid;
  grid-template-columns: 3fr 1fr 2fr;
  gap: 16px;
  padding: 12px 24px;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
  position: sticky;
  top: 0;
  z-index: 10;
}

.table-col {
  font-size: 13px;
  font-weight: 600;
  color: #595959;
  display: flex;
  align-items: center;
}

// 表体
.table-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;

  &::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }

  &::-webkit-scrollbar-track {
    background: #f5f5f5;
  }

  &::-webkit-scrollbar-thumb {
    background: #d9d9d9;
    border-radius: 3px;

    &:hover {
      background: #bfbfbf;
    }
  }
}

.table-row {
  display: grid;
  grid-template-columns: 3fr 1fr 2fr;
  gap: 16px;
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
  transition: all 0.2s ease;
  background: #fff;

  &:hover {
    background: #fafafa;
  }

  &:last-child {
    border-bottom: none;
  }
}

.cell-content {
  display: flex;
  align-items: center;
  min-width: 0;
  width: 100%;
}

.col-topic {
  min-width: 0;
  overflow: hidden;
}

.topic-name-text {
  font-size: 14px;
  color: #262626;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  width: 100%;
  display: block;
}

.type-badge,
.permission-badge {
  margin: 0;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
  border: none;
}

.qos-text,
.desc-text,
.time-text {
  font-size: 14px;
  color: #595959;
}

.desc-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.time-text {
  color: #8c8c8c;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
}

// 空状态
.topic-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

// 分页
.topic-pagination {
  padding: 16px 24px;
  border-top: 1px solid #e8e8e8;
  background: #fafafa;
  display: flex;
  justify-content: flex-end;
}

// 响应式设计
@media (max-width: 1200px) {
  .table-header,
  .table-row {
    grid-template-columns: 3fr 1fr 2fr;
  }
}

@media (max-width: 768px) {
  .topic-container {
    flex-direction: column;
  }

  .topic-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e8e8e8;
  }

  .topic-tabs {
    :deep(.ant-tabs-nav-list) {
      flex-direction: row;
      overflow-x: auto;
    }

    :deep(.ant-tabs-tab) {
      min-width: 160px;
      margin: 0 4px 0 0;
    }
  }

  .table-header,
  .table-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .table-col {
    padding: 4px 0;
  }

  .col-topic {
    order: 1;
  }

  .col-type {
    order: 2;
  }

  .col-desc {
    order: 3;
  }
}
</style>
