<template>
  <div ref="wrapRef" class="bbox-editor" :class="{ editable, dragging: !!dragState }">
    <canvas
      ref="canvasRef"
      :style="{ cursor: cursorStyle }"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointerleave="onPointerUp"
    />
    <div v-if="!imageLoaded" class="bbox-editor__placeholder">
      <Spin :spinning="true" :tip="loadingTip" size="small" />
    </div>
    <div v-if="imageLoaded && editable" class="bbox-editor__toolbar">
      <a-button size="small" :disabled="!modified" @click="resetToInitial">
        <template #icon><UndoOutlined /></template>
        还原 AI 框
      </a-button>
      <span class="bbox-editor__hint">拖动调整框位置 / 拖拽四角缩放 / 在空白处重新框选</span>
    </div>
  </div>
</template>

<script lang="ts" setup>
/**
 * 标注框修正编辑器：在整帧（或裁剪图）上展示 AI 检测框，
 * 支持拖拽平移、四角缩放、空白处重新框选；输出图像原始像素坐标。
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { UndoOutlined } from '@ant-design/icons-vue';
import { Spin } from 'ant-design-vue';

export interface EditorRect {
  x: number;
  y: number;
  w: number;
  h: number;
}

const props = withDefaults(
  defineProps<{
    src?: string;
    /** 初始（AI）框，图像像素坐标 */
    rect?: EditorRect | null;
    /** AI 原始框，用于“还原 AI 框” */
    aiRect?: EditorRect | null;
    editable?: boolean;
    accentColor?: string;
    loadingTip?: string;
  }>(),
  {
    src: '',
    rect: null,
    aiRect: null,
    editable: true,
    accentColor: '#266cfb',
    loadingTip: '图像加载中…',
  },
);

const emit = defineEmits<{
  (e: 'change', rect: EditorRect): void;
  (e: 'loaded', natural: { width: number; height: number }): void;
  (e: 'load-error'): void;
}>();

const wrapRef = ref<HTMLDivElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const imageLoaded = ref(false);
const modified = ref(false);

const naturalSize = ref({ width: 0, height: 0 });
const displaySize = ref({ width: 0, height: 0 });

const MIN_SIZE = 8; // 图像像素
const HANDLE_SIZE = 7; // 屏幕像素

let workingRect: EditorRect | null = null;
let image: HTMLImageElement | null = null;
let resizeObserver: ResizeObserver | null = null;

type DragState =
  | { mode: 'move'; startX: number; startY: number; origin: EditorRect }
  | { mode: 'resize'; corner: string; startX: number; startY: number; origin: EditorRect }
  | { mode: 'draw'; startX: number; startY: number };

const dragState = ref<DragState | null>(null);

const cursorStyle = computed(() => {
  if (!props.editable) return 'default';
  if (dragState.value) return 'grabbing';
  return 'crosshair';
});

function scale() {
  return naturalSize.value.width > 0 ? displaySize.value.width / naturalSize.value.width : 1;
}

function toImageCoord(clientX: number, clientY: number) {
  const canvas = canvasRef.value!;
  const bounds = canvas.getBoundingClientRect();
  const k = 1 / (scale() || 1);
  return {
    x: (clientX - bounds.left) * k,
    y: (clientY - bounds.top) * k,
  };
}

function clampRect(rect: EditorRect): EditorRect {
  const { width, height } = naturalSize.value;
  let { x, y, w, h } = rect;
  w = Math.max(MIN_SIZE, Math.min(w, width));
  h = Math.max(MIN_SIZE, Math.min(h, height));
  x = Math.max(0, Math.min(x, width - w));
  y = Math.max(0, Math.min(y, height - h));
  return { x, y, w, h };
}

function hitCorner(px: number, py: number): string | null {
  if (!workingRect) return null;
  const s = scale();
  const hs = HANDLE_SIZE / s / 1.2;
  const corners: Array<[string, number, number]> = [
    ['nw', workingRect.x, workingRect.y],
    ['ne', workingRect.x + workingRect.w, workingRect.y],
    ['sw', workingRect.x, workingRect.y + workingRect.h],
    ['se', workingRect.x + workingRect.w, workingRect.y + workingRect.h],
  ];
  for (const [name, cx, cy] of corners) {
    if (Math.abs(px - cx) <= hs && Math.abs(py - cy) <= hs) return name;
  }
  return null;
}

function insideRect(px: number, py: number): boolean {
  if (!workingRect) return false;
  return (
    px >= workingRect.x &&
    px <= workingRect.x + workingRect.w &&
    py >= workingRect.y &&
    py <= workingRect.y + workingRect.h
  );
}

function onPointerDown(e: PointerEvent) {
  if (!imageLoaded.value || !props.editable || !workingRect) return;
  e.preventDefault();
  canvasRef.value?.setPointerCapture?.(e.pointerId);
  const p = toImageCoord(e.clientX, e.clientY);
  const corner = hitCorner(p.x, p.y);
  if (corner) {
    dragState.value = { mode: 'resize', corner, startX: p.x, startY: p.y, origin: { ...workingRect } };
    return;
  }
  if (insideRect(p.x, p.y)) {
    dragState.value = { mode: 'move', startX: p.x, startY: p.y, origin: { ...workingRect } };
    return;
  }
  dragState.value = { mode: 'draw', startX: p.x, startY: p.y };
  workingRect = { x: p.x, y: p.y, w: 0, h: 0 };
  render();
}

function onPointerMove(e: PointerEvent) {
  if (!dragState.value || !imageLoaded.value) return;
  const p = toImageCoord(e.clientX, e.clientY);
  const state = dragState.value;
  if (state.mode === 'move') {
    const dx = p.x - state.startX;
    const dy = p.y - state.startY;
    workingRect = clampRect({
      ...state.origin,
      x: state.origin.x + dx,
      y: state.origin.y + dy,
    });
  } else if (state.mode === 'resize') {
    const o = state.origin;
    let x1 = o.x;
    let y1 = o.y;
    let x2 = o.x + o.w;
    let y2 = o.y + o.h;
    if (state.corner.includes('w')) x1 = p.x;
    if (state.corner.includes('e')) x2 = p.x;
    if (state.corner.includes('n')) y1 = p.y;
    if (state.corner.includes('s')) y2 = p.y;
    workingRect = clampRect({
      x: Math.min(x1, x2),
      y: Math.min(y1, y2),
      w: Math.abs(x2 - x1),
      h: Math.abs(y2 - y1),
    });
  } else {
    const x1 = Math.min(state.startX, p.x);
    const y1 = Math.min(state.startY, p.y);
    const w = Math.abs(p.x - state.startX);
    const h = Math.abs(p.y - state.startY);
    workingRect = clampRect({ x: x1, y: y1, w, h });
  }
  modified.value = true;
  render();
}

function onPointerUp() {
  if (!dragState.value) return;
  dragState.value = null;
  if (workingRect) {
    if (workingRect.w < MIN_SIZE || workingRect.h < MIN_SIZE) {
      workingRect = clampRect({ ...workingRect, w: MIN_SIZE, h: MIN_SIZE });
    }
    emit('change', { ...workingRect });
  }
  render();
}

function setRect(rect: EditorRect | null | undefined, markModified = true) {
  workingRect = rect ? clampRect({ ...rect }) : null;
  modified.value = markModified;
  render();
}

function resetToInitial() {
  const base = props.aiRect || props.rect;
  if (base) {
    setRect(base, false);
    emit('change', { ...base });
  }
  modified.value = false;
  render();
}

defineExpose({ setRect, resetToInitial });

function render() {
  const canvas = canvasRef.value;
  if (!canvas || !image) return;
  const { width: dw, height: dh } = displaySize.value;
  if (dw <= 0 || dh <= 0) return;
  canvas.width = dw * window.devicePixelRatio;
  canvas.height = dh * window.devicePixelRatio;
  canvas.style.width = `${dw}px`;
  canvas.style.height = `${dh}px`;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
  ctx.clearRect(0, 0, dw, dh);
  ctx.drawImage(image, 0, 0, dw, dh);

  if (!workingRect) return;
  const s = scale();
  const rx = workingRect.x * s;
  const ry = workingRect.y * s;
  const rw = workingRect.w * s;
  const rh = workingRect.h * s;

  // 遮罩暗化框外区域，突出提取区域
  ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
  ctx.fillRect(0, 0, dw, ry);
  ctx.fillRect(0, ry + rh, dw, dh - ry - rh);
  ctx.fillRect(0, ry, rx, rh);
  ctx.fillRect(rx + rw, ry, dw - rx - rw, rh);

  ctx.strokeStyle = props.accentColor;
  ctx.lineWidth = 2;
  ctx.strokeRect(rx, ry, rw, rh);

  if (props.editable) {
    ctx.fillStyle = '#fff';
    ctx.strokeStyle = props.accentColor;
    ctx.lineWidth = 1.5;
    const hs = HANDLE_SIZE;
    for (const [cx, cy] of [
      [rx, ry],
      [rx + rw, ry],
      [rx, ry + rh],
      [rx + rw, ry + rh],
    ]) {
      ctx.beginPath();
      ctx.rect(cx - hs / 2, cy - hs / 2, hs, hs);
      ctx.fill();
      ctx.stroke();
    }
  }
}

function updateDisplaySize() {
  const wrap = wrapRef.value;
  if (!wrap || !image) return;
  const availW = wrap.clientWidth;
  const availH = wrap.clientHeight;
  if (availW <= 0 || availH <= 0) return;
  const { width: nw, height: nh } = naturalSize.value;
  if (nw <= 0 || nh <= 0) return;
  const fit = Math.min(availW / nw, availH / nh);
  displaySize.value = { width: Math.floor(nw * fit), height: Math.floor(nh * fit) };
  render();
}

function loadImage() {
  imageLoaded.value = false;
  workingRect = null;
  if (!props.src) return;
  const img = new Image();
  img.crossOrigin = 'anonymous';
  img.onload = () => {
    image = img;
    naturalSize.value = { width: img.naturalWidth, height: img.naturalHeight };
    imageLoaded.value = true;
    updateDisplaySize();
    if (props.rect) {
      setRect(props.rect, false);
    }
    emit('loaded', { ...naturalSize.value });
  };
  img.onerror = () => {
    imageLoaded.value = false;
    emit('load-error');
  };
  img.src = props.src;
}

onMounted(() => {
  resizeObserver = new ResizeObserver(() => updateDisplaySize());
  if (wrapRef.value) resizeObserver.observe(wrapRef.value);
  loadImage();
});

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  resizeObserver = null;
});

watch(() => props.src, loadImage);
watch(
  () => props.rect,
  (val) => {
    if (!dragState.value && val) {
      // 父组件回传的框仅同步位置，不改变用户修改标记
      workingRect = clampRect({ ...val });
      render();
    }
  },
);
</script>

<style lang="less" scoped>
.bbox-editor {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  min-height: 220px;
  overflow: hidden;
  background:
    radial-gradient(rgba(0, 0, 0, 0.14) 1px, transparent 1px) #f5f6f8;
  background-size: 14px 14px;

  canvas {
    display: block;
    max-width: 100%;
  }

  &__placeholder {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__toolbar {
    position: absolute;
    top: 10px;
    left: 10px;
    right: 10px;
    z-index: 3;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  &__hint {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.92);
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
}
</style>
