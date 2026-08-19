<template>
  <div
    class="node-item-card"
    :class="{
      'node-item-card--compact': compact,
      'node-item-card--swimlane': swimlane,
      'node-item-card--swimlane-central': swimlane && central,
      'node-item-card--inlane': inlane,
      'node-item-card--selected': selected,
    }"
    @mouseenter="hoverId = item.id ?? null"
    @mouseleave="hoverId = null"
  >
    <div
      class="node-item-card__cover"
      :class="[
        getNodeRoleVisual(primaryNodeFunction(item)).coverClass,
        item.status ? `node-item-card__cover--${item.status}` : '',
      ]"
      @click="emit('view', item)"
    >
      <div class="node-item-card__cover-inner">
        <NodeRoleIcon
          :role="primaryNodeFunction(item)"
          :size="compact ? 'md' : central ? 'lg' : 'ml'"
        />
      </div>
      <div class="node-item-card__badges" @click.stop>
        <NodeMetaBadge type="role" :role="primaryNodeFunction(item)" :label="formatNodeFunctions(item)" size="sm" />
        <NodeMetaBadge type="status" :status="item.status" size="sm" />
      </div>
      <div v-if="selectable" class="node-item-card__checkbox" @click.stop>
        <Checkbox
          :checked="selected"
          @change="(e) => emit('select', item, e.target.checked)"
        />
      </div>
      <div
        v-show="hoverId === item.id && showOverlay"
        class="node-item-card__overlay"
        @click.stop
      >
        <div class="overlay-actions">
          <Tooltip v-if="item.status === 'pending'" :title="NODE_TERM.continueOnboard">
            <button class="overlay-btn" @click="emit('continueSetup', item)">
              <RocketOutlined />
            </button>
          </Tooltip>
          <Tooltip title="查看详情">
            <button class="overlay-btn" @click="emit('view', item)">
              <EyeOutlined />
            </button>
          </Tooltip>
          <Tooltip v-if="!isPlatformNode(item) && manageable" title="编辑">
            <button class="overlay-btn" @click="emit('edit', item)">
              <EditOutlined />
            </button>
          </Tooltip>
          <Popconfirm
            v-if="!isPlatformNode(item) && manageable"
            title="确认删除该节点？"
            @confirm="emit('delete', item)"
          >
            <Tooltip title="删除">
              <button class="overlay-btn overlay-btn--danger">
                <DeleteOutlined />
              </button>
            </Tooltip>
          </Popconfirm>
        </div>
      </div>
    </div>

    <div class="node-item-card__body">
      <h3 class="node-item-card__title" :title="item.name" @click="emit('view', item)">
        <span>{{ item.name }}</span>
      </h3>
      <p v-if="metaText" class="node-item-card__meta" :title="metaText">
        {{ metaText }}
      </p>
      <div v-if="isPlatformNode(item)" class="node-item-card__tags">
        <NodeMetaBadge type="scope" size="xs" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue';
import { Checkbox, Popconfirm, Tooltip } from 'ant-design-vue';
import { DeleteOutlined, EditOutlined, EyeOutlined, RocketOutlined } from '@ant-design/icons-vue';
import type { ComputeNodeVO } from '@/api/device/node';
import {
  NODE_TERM,
  primaryNodeFunction,
  formatNodeFunctions,
} from '../../utils/constants';
import { getNodeRoleVisual } from '../../utils/nodeAssets';
import { isPlatformNode } from '../../utils/platformNode';
import NodeMetaBadge from '../NodeMetaBadge/index.vue';
import NodeRoleIcon from '../NodeRoleIcon/index.vue';

defineOptions({ name: 'NodeItemCard' });

const props = withDefaults(
  defineProps<{
    item: ComputeNodeVO;
    compact?: boolean;
    swimlane?: boolean;
    central?: boolean;
    inlane?: boolean;
    selectable?: boolean;
    selected?: boolean;
    manageable?: boolean;
    showOverlay?: boolean;
    metaText?: string;
  }>(),
  {
    compact: false,
    swimlane: false,
    central: false,
    inlane: false,
    selectable: false,
    selected: false,
    manageable: true,
    showOverlay: true,
  },
);

const emit = defineEmits<{
  view: [node: ComputeNodeVO];
  edit: [node: ComputeNodeVO];
  delete: [node: ComputeNodeVO];
  continueSetup: [node: ComputeNodeVO];
  select: [node: ComputeNodeVO, checked: boolean];
}>();

const hoverId = ref<number | null>(null);

const metaText = computed(() => {
  if (props.metaText !== undefined) return props.metaText;
  const parts: string[] = [];
  if (props.item.host) parts.push(props.item.host);
  if (!parts.length) return props.item.id != null ? `ID: ${props.item.id}` : '';
  return parts.join('  |  ');
});
</script>

<style lang="less" scoped>
@import '../../utils/nodeRoleTheme.less';
@import '../../utils/theme.less';

@cover-height: 200px;
@cover-height-compact: 140px;
@cover-height-swimlane: 132px;
@cover-height-swimlane-central: 140px;
@body-min-height: 86px;
@body-min-height-swimlane: 90px;

.node-item-card {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  min-height: @cover-height + @body-min-height;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(24, 24, 24, 0.06);
  overflow: hidden;
  transition: box-shadow 0.25s ease, transform 0.25s ease, border-color 0.2s;
  border: 1px solid #f0f0f0;
  cursor: default;

  &:hover {
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
    transform: translateY(-1px);
  }

  &--compact {
    min-height: @cover-height-compact + @body-min-height;

    .node-item-card__cover {
      height: @cover-height-compact;
    }
  }

  &--swimlane {
    min-height: @cover-height-swimlane + @body-min-height-swimlane;
    border-radius: 12px;

    &:hover {
      transform: translateY(-3px);
      box-shadow: 0 8px 24px rgba(38, 108, 251, 0.12);
    }

    .node-item-card__cover {
      height: @cover-height-swimlane;
    }

    .node-item-card__cover-inner {
      padding: 0 14px 6px;

      &::before {
        min-height: 48px;
      }
    }

    .node-item-card__body {
      min-height: @body-min-height-swimlane;
      padding: 14px 14px 16px;
    }

    .node-item-card__title {
      font-size: 15px;
      margin-bottom: 10px;
      line-height: 1.4;
    }

    .node-item-card__meta {
      font-size: 12px;
      line-height: 1.55;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .overlay-btn {
      width: 36px;
      height: 36px;
      font-size: 16px;
    }
  }

  &--swimlane-central {
    min-height: @cover-height-swimlane-central + @body-min-height-swimlane + 4px;

    .node-item-card__cover {
      height: @cover-height-swimlane-central;
    }

    .node-item-card__cover-inner {
      padding: 0 14px 8px;

      &::before {
        min-height: 52px;
      }
    }

    .node-item-card__body {
      padding: 16px 14px 18px;
    }

    .node-item-card__title {
      font-size: 16px;
    }

    .node-item-card__meta {
      font-size: 13px;
    }
  }

  &--inlane {
    height: 100%;
    background: #fff;
    border: 1px solid @node-border;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);

    &:hover {
      border-color: fade(@node-primary, 28%);
      box-shadow: 0 6px 20px rgba(38, 108, 251, 0.1);
      transform: translateY(-2px);
    }
  }

  &--inlane.node-item-card--swimlane-central {
    border-color: fade(@node-primary, 22%);
    box-shadow: 0 4px 18px rgba(38, 108, 251, 0.1);

    &:hover {
      border-color: fade(@node-primary, 40%);
      box-shadow: 0 8px 28px rgba(38, 108, 251, 0.14);
      transform: translateY(-3px);
    }
  }

  &--inlane.node-item-card--selected {
    border-color: @node-primary;
    box-shadow: 0 0 0 2px fade(@node-primary, 12%);
  }

  &--selected {
    border-color: #266cfb;
    box-shadow: 0 0 0 2px rgba(38, 108, 251, 0.12);
  }
}

.node-item-card__cover {
  position: relative;
  width: 100%;
  height: @cover-height;
  flex-shrink: 0;
  overflow: hidden;
  cursor: pointer;
  transition: background 0.2s ease;

  &--compute {
    background: linear-gradient(180deg, @node-compute-tile-start 0%, @node-compute-tile-end 100%);
  }

  &--media {
    background: linear-gradient(180deg, @node-media-tile-start 0%, @node-media-tile-end 100%);
  }

  &--mqtt {
    background: linear-gradient(180deg, @node-mqtt-tile-start 0%, @node-mqtt-tile-end 100%);
  }

  &--hybrid {
    background: linear-gradient(180deg, @node-hybrid-tile-start 0%, @node-hybrid-tile-end 100%);
  }

  &--storage {
    background: linear-gradient(180deg, @node-storage-tile-start 0%, @node-storage-tile-end 100%);
  }

  &--offline .node-item-card__cover-inner {
    opacity: 0.72;
    filter: grayscale(0.35);
  }

  &--pending .node-item-card__cover-inner {
    opacity: 0.88;
  }
}

.node-item-card__cover-inner {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  padding: 0 14px 6px;
  box-sizing: border-box;
  transition: opacity 0.2s ease, filter 0.2s ease;

  &::before {
    content: '';
    display: block;
    flex: 1 1 0;
    min-height: 50px;
    width: 100%;
    pointer-events: none;
  }
}

.node-item-card__badges {
  position: absolute;
  top: 12px;
  right: 12px;
  left: 12px;
  z-index: 2;
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  min-height: 22px;
  padding-bottom: 4px;
  pointer-events: none;

  :deep(.node-meta-badge) {
    flex-shrink: 0;
    pointer-events: auto;
  }
}

.node-item-card__checkbox {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 4;
}

.node-item-card__overlay {
  position: absolute;
  inset: 0;
  z-index: 3;
  border-radius: 6px 6px 0 0;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
  pointer-events: none;
}

.overlay-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
  padding: 0 8px;
  pointer-events: auto;
}

.overlay-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  color: #266cfb;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s, transform 0.2s;

  &:hover {
    background: #fff;
    transform: scale(1.08);
  }

  &--danger {
    color: #f5222d;

    &:hover {
      background: #fff1f0;
    }
  }
}

.node-item-card__body {
  flex: 1;
  min-height: @body-min-height;
  padding: 14px 14px 16px;
  box-sizing: border-box;
}

.node-item-card__title {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.45;
  color: #181818;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  overflow: hidden;
  cursor: pointer;

  &:hover {
    color: #266cfb;
  }
}

.node-item-card--compact .node-item-card__title {
  font-size: 14px;
}

.node-item-card__meta {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: #999;
  white-space: normal;
  word-break: break-all;
}

.node-item-card__tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}
</style>
