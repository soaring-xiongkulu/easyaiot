<template>
  <div class="alert-notification-config">
    <!-- 启用告警通知开关 -->
    <a-form-item label="启用告警通知" v-if="showNotificationSwitch">
      <a-switch
        v-model:checked="notificationEnabled"
        checked-children="是"
        un-checked-children="否"
        @change="handleNotificationEnabledChange"
        :disabled="isViewMode"
      />
    </a-form-item>

    <!-- 通知渠道配置 -->
    <div v-if="notificationEnabled">
      <a-form-item label="通知渠道" :rules="[{ required: true, message: '请选择至少一个通知渠道' }]">
        <a-select
          v-model:value="selectedChannels"
          mode="multiple"
          :placeholder="'请选择通知渠道（可多选）'"
          :disabled="isViewMode"
          @change="handleChannelsChange"
          style="width: 100%"
        >
          <a-select-option
            v-for="channel in availableChannels"
            :key="channel.value"
            :value="channel.value"
          >
            {{ channel.label }}
          </a-select-option>
        </a-select>
      </a-form-item>

      <!-- 每个渠道的模板选择 -->
      <div v-for="channel in selectedChannels" :key="channel" class="channel-template-config">
        <a-form-item
          :label="`${getChannelLabel(channel)}模板`"
          :rules="[{ required: true, message: `请选择${getChannelLabel(channel)}模板` }]"
        >
          <a-select
            v-model:value="channelTemplates[channel]"
            :placeholder="`请选择${getChannelLabel(channel)}模板`"
            :loading="templateLoading[channel]"
            show-search
            :filter-option="filterTemplateOption"
            @change="handleTemplateChange(channel, $event)"
            :disabled="isViewMode"
            style="width: 100%"
          >
            <a-select-option
              v-for="template in templates[channel]"
              :key="template.id"
              :value="template.id"
            >
              {{ template.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </div>

      <!-- 告警抑制时间 -->
      <a-form-item label="告警抑制时间（秒）" help="防止频繁通知，默认300秒（5分钟）">
        <a-input-number
          v-model:value="suppressTime"
          :min="0"
          :max="3600"
          :step="60"
          placeholder="300"
          :disabled="isViewMode"
          style="width: 100%"
        />
      </a-form-item>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue';
import { useMessage } from '@/hooks/web/useMessage';
import { notifyTemplateQueryByType } from '@/api/device/notice';

interface Props {
  modelValue?: {
    enabled?: boolean;
    channels?: Array<{
      method: string;
      template_id: string | number;
      template_name?: string;
    }>;
    suppress_time?: number;
  };
  alertEventEnabled?: boolean;
  isViewMode?: boolean;
  showNotificationSwitch?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => ({
    enabled: false,
    channels: [],
    suppress_time: 300,
  }),
  alertEventEnabled: false,
  isViewMode: false,
  showNotificationSwitch: true,
});

const emit = defineEmits<{
  'update:modelValue': [value: any];
}>();

const { createMessage } = useMessage();

// 组件挂载状态标志
const isMounted = ref(false);

// 可用通知渠道
const availableChannels = [
  { label: '短信', value: 'sms' },
  { label: '邮件', value: 'email' },
  { label: '企业微信', value: 'wxcp' },
  { label: 'HTTP', value: 'http' },
  { label: '钉钉', value: 'ding' },
  { label: '飞书', value: 'feishu' },
];

// 通知渠道到消息类型的映射
const channelToMsgType: Record<string, number> = {
  sms: 1, // 阿里云短信
  email: 3, // 邮件
  wxcp: 4, // 企业微信
  http: 5, // HTTP
  ding: 6, // 钉钉
  feishu: 7, // 飞书
};

// 通知启用状态
const notificationEnabled = ref(props.modelValue?.enabled || false);

// 选中的渠道
const selectedChannels = ref<string[]>(
  props.modelValue?.channels?.map((c) => c.method) || []
);

// 每个渠道的模板ID
const channelTemplates = ref<Record<string, string | number>>({});

// 模板列表（按渠道分组）
const templates = ref<Record<string, any[]>>({});

// 模板加载状态
const templateLoading = ref<Record<string, boolean>>({});

// 抑制时间
const suppressTime = ref(props.modelValue?.suppress_time || 300);

// 初始化渠道模板映射
const initChannelTemplates = () => {
  if (props.modelValue?.channels) {
    props.modelValue.channels.forEach((channel) => {
      channelTemplates.value[channel.method] = channel.template_id;
    });
  }
};

// 获取渠道标签
const getChannelLabel = (channel: string) => {
  return availableChannels.find((c) => c.value === channel)?.label || channel;
};

// 加载模板列表
const loadTemplates = async (channel: string) => {
  if (templates.value[channel]?.length) {
    return; // 已加载
  }

  templateLoading.value[channel] = true;
  try {
    const msgType = channelToMsgType[channel];
    if (!msgType) {
      console.warn(`未知的通知渠道: ${channel}`);
      return;
    }

    const response = await notifyTemplateQueryByType({ msgType });
    // 处理响应：可能是{code: 0, data: [...]}格式，也可能是直接返回数组
    if (response) {
      if (response.code === 0 && response.data) {
        templates.value[channel] = Array.isArray(response.data) ? response.data : [];
      } else if (Array.isArray(response)) {
        // 如果直接返回数组
        templates.value[channel] = response;
      } else {
        templates.value[channel] = [];
        console.warn(`加载${getChannelLabel(channel)}模板失败:`, response?.msg || '未知错误');
      }
    } else {
      templates.value[channel] = [];
      console.warn(`加载${getChannelLabel(channel)}模板失败: 响应为空`);
    }
  } catch (error) {
    console.error(`加载${getChannelLabel(channel)}模板失败:`, error);
    templates.value[channel] = [];
  } finally {
    templateLoading.value[channel] = false;
  }
};

// 渠道变化处理
const handleChannelsChange = (channels: string[]) => {
  // 加载新选中渠道的模板
  channels.forEach((channel) => {
    if (!templates.value[channel]) {
      loadTemplates(channel);
    }
  });

  // 移除未选中渠道的模板
  Object.keys(channelTemplates.value).forEach((channel) => {
    if (!channels.includes(channel)) {
      delete channelTemplates.value[channel];
    }
  });

  updateModelValue();
};

// 模板变化处理
const handleTemplateChange = (channel: string, templateId: string | number) => {
  channelTemplates.value[channel] = templateId;
  updateModelValue();
};

// 通知启用状态变化
const handleNotificationEnabledChange = (enabled: boolean) => {
  if (!enabled) {
    selectedChannels.value = [];
    channelTemplates.value = {};
  }
  updateModelValue();
};

// 更新模型值
const updateModelValue = () => {
  // 如果组件已卸载，不执行更新
  if (!isMounted.value) {
    return;
  }
  
  const channels = selectedChannels.value.map((method) => {
    const templateId = channelTemplates.value[method];
    const template = templates.value[method]?.find((t) => t.id === templateId);
    return {
      method,
      template_id: templateId,
      template_name: template?.name || '',
    };
  });

  emit('update:modelValue', {
    enabled: notificationEnabled.value,
    channels,
    suppress_time: suppressTime.value,
  });
};


// 模板过滤
const filterTemplateOption = (input: string, option: any) => {
  return option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0;
};

// 监听props变化
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      notificationEnabled.value = newVal.enabled || false;
      selectedChannels.value = newVal.channels?.map((c) => c.method) || [];
      suppressTime.value = newVal.suppress_time || 300;
      initChannelTemplates();
    }
  },
  { deep: true, immediate: true }
);

// 监听告警事件启用状态
watch(
  () => props.alertEventEnabled,
  (enabled) => {
    if (!enabled) {
      notificationEnabled.value = false;
      selectedChannels.value = [];
      channelTemplates.value = {};
      updateModelValue();
    }
  }
);

// 监听抑制时间变化
watch(suppressTime, () => {
  updateModelValue();
});

onMounted(() => {
  isMounted.value = true;
  // 初始化已选中渠道的模板
  selectedChannels.value.forEach((channel) => {
    loadTemplates(channel);
  });
});

onBeforeUnmount(() => {
  isMounted.value = false;
});
</script>

<style lang="less" scoped>
.alert-notification-config {
  .channel-template-config {
    margin-bottom: 16px;
  }

  :deep(.ant-form-item) {
    margin-bottom: 20px;
  }

  :deep(.ant-form-item-label) {
    padding-bottom: 4px;
  }
}
</style>

