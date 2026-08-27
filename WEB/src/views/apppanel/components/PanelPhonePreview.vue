<template>
  <div class="phone-preview" :class="{empty: !widgets.length}">
    <div class="pp-status"><span>9:41</span><span class="pp-bars">●●●</span></div>
    <div class="pp-navbar">
      <span class="pp-back">‹</span>
      <span class="pp-title">{{ templateName || '设备控制台' }}</span>
      <span class="pp-online">在线</span>
    </div>
    <div class="pp-body">
      <div
        v-for="w in widgets"
        :key="w.id"
        class="pp-card"
        :class="{half: w.span === 'half'}"
      >
        <template v-if="w.type === 'switch'">
          <span class="pp-label">{{ w.title }}</span>
          <span class="pp-switch"><i></i></span>
        </template>
        <template v-else-if="w.type === 'slider' || w.type === 'number'">
          <div class="pp-col">
            <span class="pp-label">{{ w.title }}</span>
            <span class="pp-value">42<span class="pp-unit">{{ w.unit }}</span></span>
          </div>
          <div v-if="w.type === 'slider'" class="pp-slider"><i style="width: 42%"></i></div>
        </template>
        <template v-else-if="w.type === 'status'">
          <span class="pp-label">{{ w.title }}</span>
          <span class="pp-tag" :style="{background: optionColor(w)}">{{ optionLabel(w) }}</span>
        </template>
        <template v-else-if="w.type === 'text'">
          <span class="pp-label">{{ w.title }}</span>
          <span class="pp-value">25.4<span class="pp-unit">{{ w.unit }}</span></span>
        </template>
        <template v-else-if="w.type === 'button'">
          <span class="pp-btn">{{ w.title }}</span>
        </template>
        <template v-else-if="w.type === 'chart'">
          <div class="pp-col">
            <span class="pp-label">{{ w.title }}</span>
            <span class="pp-value">42<span class="pp-unit">{{ w.unit }}</span></span>
          </div>
          <svg class="pp-chart" viewBox="0 0 120 34" preserveAspectRatio="none">
            <polygon fill="#2f6bff18" points="0,28 16,22 32,26 48,16 64,20 80,12 96,16 120,9 120,34 0,34" />
            <polyline fill="none" stroke="#2f6bff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"
                      points="0,28 16,22 32,26 48,16 64,20 80,12 96,16 120,9" />
            <circle cx="120" cy="9" r="2" fill="#2f6bff" />
          </svg>
        </template>
        <template v-else-if="w.type === 'gauge'">
          <div class="pp-col">
            <span class="pp-label">{{ w.title }}</span>
            <span class="pp-value">68<span class="pp-unit">{{ w.unit }}</span></span>
          </div>
          <div class="pp-gauge"><i style="width: 68%"></i></div>
        </template>
        <template v-else-if="w.type === 'progress'">
          <div class="pp-col">
            <span class="pp-label">{{ w.title }}</span>
            <span class="pp-value">68<span class="pp-unit">{{ w.unit }}</span></span>
          </div>
          <div class="pp-progress"><i style="width: 68%"></i></div>
        </template>
        <template v-else-if="w.type === 'video'">
          <span class="pp-label">{{ w.title }}</span>
          <span class="pp-video">▶ 实时画面</span>
        </template>
      </div>
      <div v-if="!widgets.length" class="pp-empty">空模板<br />暂无组件</div>
    </div>
  </div>
</template>

<script lang="ts" setup name="PanelPhonePreview">
import {computed} from 'vue';

const props = defineProps({
  schema: {type: String, default: ''},
  templateName: {type: String, default: ''},
});

// 解析模板 schema 的组件列表
const widgets = computed<any[]>(() => {
  try {
    const parsed = props.schema ? JSON.parse(props.schema) : null;
    return parsed?.pages?.[0]?.widgets ?? [];
  } catch (e) {
    return [];
  }
});

// 迷你预览的枚举映射（与编辑器一致）
const parseEnumText = (enumText?: string) => {
  if (!enumText) return [];
  return enumText
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [label, value, color] = line.split(':').map((s) => s.trim());
      return {label, value, ...(color ? {color} : {})};
    });
};

function optionLabel(w): string {
  const configOpts = w.config?.options;
  if (Array.isArray(configOpts) && configOpts.length) return configOpts[0].label;
  return parseEnumText(w.enumText)[0]?.label || '--';
}

function optionColor(w): string {
  const configOpts = w.config?.options;
  if (Array.isArray(configOpts) && configOpts[0]?.color) return configOpts[0].color;
  return parseEnumText(w.enumText)[0]?.color || '#2f6bff';
}
</script>

<style lang="less" scoped>
// 手机竖屏比例（9:16，iPhone 经典屏比），由外部容器定高、自身按比例定宽
.phone-preview {
  height: 100%;
  width: auto;
  max-width: 100%;
  aspect-ratio: 9 / 16;
  background: linear-gradient(180deg, #eef3fb 0%, #f7f9fc 60%);
  border: 5px solid #10131a;
  border-radius: 22px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  &.empty {
    align-items: center;
    justify-content: center;
  }
}

.pp-status {
  display: flex;
  justify-content: space-between;
  padding: 5px 12px 0;
  font-size: 8px;
  font-weight: 600;
  color: #1a1d29;
  flex-shrink: 0;

  .pp-bars {
    letter-spacing: 1px;
  }
}

.pp-navbar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  flex-shrink: 0;

  .pp-back {
    font-size: 14px;
    line-height: 1;
  }

  .pp-title {
    flex: 1;
    text-align: center;
    font-size: 9px;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .pp-online {
    font-size: 7px;
    color: #16a377;
    background: rgba(22, 163, 119, 0.12);
    border-radius: 99px;
    padding: 1px 6px;
  }
}

.pp-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 3px 8px 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  align-content: flex-start;

  .pp-empty {
    width: 100%;
    text-align: center;
    color: rgba(0, 0, 0, 0.3);
    font-size: 9px;
    line-height: 1.8;
    margin-top: 48px;
  }
}

.pp-card {
  width: 100%;
  background: #fff;
  border-radius: 8px;
  padding: 6px 8px;
  box-shadow: 0 1px 4px rgba(31, 45, 74, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;

  &.half {
    width: calc(50% - 3px);
  }

  .pp-label {
    font-size: 8px;
    font-weight: 600;
    color: #1a1d29;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .pp-value {
    font-size: 11px;
    font-weight: 700;
    color: #2f6bff;

    .pp-unit {
      font-size: 7px;
      font-weight: 400;
      color: #98a2b3;
      margin-left: 1px;
    }
  }

  .pp-col {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
}

.pp-switch {
  width: 24px;
  height: 13px;
  border-radius: 99px;
  background: linear-gradient(135deg, #4a8bff, #2f6bff);
  position: relative;
  flex-shrink: 0;

  i {
    position: absolute;
    right: 1px;
    top: 1px;
    width: 11px;
    height: 11px;
    background: #fff;
    border-radius: 50%;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  }
}

.pp-slider {
  height: 4px;
  border-radius: 2px;
  background: #edeff5;
  overflow: hidden;

  i {
    display: block;
    height: 100%;
    border-radius: 2px;
    background: linear-gradient(90deg, #4a8bff, #2f6bff);
    position: relative;

    &::after {
      content: '';
      position: absolute;
      right: -3px;
      top: 50%;
      transform: translateY(-50%);
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #fff;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
    }
  }
}

.pp-tag {
  color: #fff;
  font-size: 7px;
  border-radius: 99px;
  padding: 1px 6px;
  white-space: nowrap;
  flex-shrink: 0;
}

.pp-btn {
  background: linear-gradient(135deg, #4a8bff, #2f6bff);
  color: #fff;
  border-radius: 99px;
  padding: 4px 14px;
  font-size: 8px;
  font-weight: 600;
  margin: 0 auto;
}

.pp-video {
  height: 52px;
  border-radius: 6px;
  background: #10131a;
  color: rgba(255, 255, 255, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 8px;
  flex: 1;
}

.pp-chart {
  width: 100%;
  height: 30px;
  display: block;
}

.pp-gauge {
  width: 100%;
  height: 26px;
  border-radius: 26px 26px 0 0;
  background: #edeff5;
  overflow: hidden;

  i {
    display: block;
    height: 100%;
    width: 68%;
    border-radius: 26px 26px 0 0;
    background: linear-gradient(90deg, #4a8bff, #2f6bff);
  }
}

.pp-progress {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #edeff5;
  overflow: hidden;

  i {
    display: block;
    height: 100%;
    border-radius: 3px;
    background: linear-gradient(90deg, #4a8bff, #2f6bff);
  }
}
</style>
