<template>
  <div class="app-container">
    <a-layout has-sider sider-placement="left">
      <div class="left-content">
        <!-- 面板控制-->
        <div style="position: absolute; z-index: 999">
          <a-button @click="!collapsed1?collapsedHandle1():expandHandle1()">组件</a-button>
          <a-button @click="!collapsed2?collapsedHandle2():expandHandle2()">配置</a-button>
        </div>
        <!-- 左侧组件 -->
        <a-layout-sider
          style="margin-top: 40px"
          collapse-mode="transform"
          :collapsed-width="0"
          :width="250"
          :collapsed="collapsed1"
          :native-scrollbar="false"
          show-trigger="bar"
          @collapse="collapsedHandle1"
          @expand="expandHandle1"
        >
          <div class="left-side">
            <div class="iot-content-charts-item-box">
              <div
                class="item-box"
                v-for="(item, index) in menuOptions"
                :key="item['list'][0].title"
                draggable
                @dragstart="!item['list'][0].disabled && dragStartHandle($event, item['list'][0])"
                @dragend="!item['list'][0].disabled && dragendHandle()"
                @dblclick="dblclickHandle(item['list'][0])"
                @click="clickHandle(item['list'][0])"
              >
                <div class="list-header">
                  <span class="text">{{ item['list'][0]['title'] }}</span>
                </div>

                <div class="list-center">
                  <img class="list-img" :alt="item['list'][0]['title']" :src=BAR_X>
                </div>
              </div>
            </div>
          </div>
        </a-layout-sider>
      </div>

      <!-- 中央画板 -->
      <a-layout-content>
        <div id="iot-chart-edit-layout" class="iot-content-box"
             @mousedown="mousedownHandleUnStop"
             @drop="dragHandle"
             @dragover="dragoverHandle"
             @dragenter="dragoverHandle"
        >
          <div class="iot-sketch-rule">
            <sketch-rule
              v-if="sketchRuleReDraw"
              :thick="thick"
              :scale="scale"
              :width="canvasBox().width"
              :height="canvasBox().height"
              :startX="startX"
              :startY="startY"
              :lines="lines"
              :palette="paletteStyle"
            >
            </sketch-rule>
            <div ref="$app" class="edit-screens" @scroll="handleScroll">
              <div ref="$container" class="edit-screen-container"
                   :style="{ width: containerWidth }">
                <div
                  ref="refSketchRuleBox"
                  class="canvas"
                  @mousedown="dragCanvas"
                  :style="{ marginLeft: '-' + (canvasBox().width / 2 - 25) + 'px' }"
                >
                  <div :style="{ pointerEvents: isPressSpace ? 'none' : 'auto' }">
                    <div id="iot-chart-edit-content" @contextmenu="handleContextMenu">
                      <div class="iot-edit-range iot-transition" :style="rangeStyle"
                           @mousedown="mousedownBoxSelect($event, undefined)">
                        <!-- 滤镜预览 -->
                        <div
                          :style="{
                            ...getFilterStyle(chartEditStore.getEditCanvasConfig),
                            ...rangeStyle2
                          }"
                        >
                          <!-- 图表 -->
                          <div v-for="(item, index) in chartEditStore.getComponentList"
                               :key="item.id">
                            <div class="iot-shape-box"
                                 :class="{ lock: lock(item), hide: hide(item) }"
                                 :data-id="item.id"
                                 :index="index"
                                 :style="{
                                  ...useComponentStyle(item.attr, index),
                                  ...getBlendModeStyle(item.styles) as any
                                }"
                                 @click="mouseClickHandle($event, item)"
                                 @mousedown="mousedownHandle($event, item)"
                                 @mouseenter="mouseenterHandle($event, item)"
                                 @mouseleave="mouseleaveHandle($event, item)"
                                 @contextmenu="handleContextMenu($event, item, optionsHandle)"
                            >
                              <!-- VInputsDate-->
                              <component
                                class="edit-content-chart"
                                :class="animationsClass(item.styles.animations)"
                                :is="item.chartConfig.chartKey"
                                :chartConfig="item"
                                :themeSetting="themeSetting"
                                :themeColor="themeColor"
                                :style="{
                                  ...useSizeStyle(item.attr),
                                  ...getFilterStyle(item.styles),
                                  ...getTransformStyle(item.styles)
                                }"
                              ></component>
                              <!-- 锚点 -->
                              <template v-if="!hiddenPoint">
                                <div
                                  :class="`shape-point ${point}`"
                                  v-for="(point, index) in select(item) ? pointList : []"
                                  :key="index"
                                  :style="usePointStyle(point, index, item.attr, cursorResize)"
                                  @mousedown="useMousePointHandle($event, point, item.attr)"
                                ></div>
                              </template>
                              <!-- 选中 -->
                              <div class="shape-modal" :style="useSizeStyle(item.attr)">
                                <div class="shape-modal-select"
                                     :class="{ active: select(item) }"></div>
                                <div class="shape-modal-change"
                                     :class="{ selectActive: select(item), hoverActive: hover(item) }"></div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </a-layout-content>

      <!-- 右侧组件 -->
      <a-layout-sider
        collapse-mode="transform"
        :collapsed-width="0"
        :width="350"
        :collapsed="collapsed2"
        :native-scrollbar="false"
        show-trigger="bar"
        @collapse="collapsedHandle2"
        @expand="expandHandle2"
      >
        12111
      </a-layout-sider>
    </a-layout>
  </div>
</template>
<script lang="ts" setup>
import {computed, onMounted, onUnmounted, provide, reactive, ref, toRefs, watch} from 'vue'
import {listen} from 'dom-helpers'
import {useDesignStore} from '@/store/modules/designStore/designStore'
import {useChartEditStore} from '@/store/modules/chartEditStore/chartEditStore'
import {useChartLayoutStore} from '@/store/modules/chartLayoutStore/chartLayoutStore'
import {ChartLayoutStoreEnum} from '@/store/modules/chartLayoutStore/chartLayoutStore.d'
import {EditCanvasTypeEnum} from '@/store/modules/chartEditStore/chartEditStore.d'
import {
  dragHandle,
  dragoverHandle,
  mousedownBoxSelect,
  mousedownHandleUnStop,
  useMouseHandle,
  useMousePointHandle
} from '@/hooks/design/useDrag.hook'
import throttle from 'lodash/throttle'
import {useContextMenu} from '@/hooks/design/useContextMenu.hook'
import {useLayout} from '@/hooks/design/useLayout.hook'
import {SCALE_KEY} from '@/hooks/design/useScale.hook'
import {useAsideHook} from '@/hooks/design/useAside.hook'

import BAR_X from "@/assets/images/chart/charts/bar_x.png"
import {componentInstall} from "@/utils/components";
import {createComponent, fetchChartComponent, fetchConfigComponent} from "@/design/packages/index";
import {DragKeyEnum} from "@/enums/editPageEnum";
import {
  animationsClass,
  getBlendModeStyle,
  getFilterStyle,
  getTransformStyle,
  JSONStringify
} from "@/utils";
import {omit} from "lodash-es";
import {useComponentStyle, usePointStyle} from "@/hooks/design/useStyle.hook";

import {CreateComponentGroupType, CreateComponentType} from '@/design/packages/index.d'
import {useAddKeyboard} from "@/hooks/design/useKeyboard.hook";

const {getDetails} = toRefs(useChartLayoutStore())

const {
  menuOptions
} = useAsideHook()

// 编辑时注入scale变量，消除警告
provide(SCALE_KEY, null)

// 布局处理
useLayout(async () => {
})

// 点击事件
const {mouseenterHandle, mouseleaveHandle, mousedownHandle, mouseClickHandle} = useMouseHandle()

const {handleContextMenu} = useContextMenu()

const chartEditStore = useChartEditStore()
const chartLayoutStore = useChartLayoutStore()
const designStore = useDesignStore()

const thick = 20
let prevMoveXValue = [0, 0]
let prevMoveYValue = [0, 0]

const $app = ref<HTMLElement | null>(null);
const sketchRuleReDraw = ref(true)
const refSketchRuleBox = ref()
const $container = ref()
const isPressSpace = ref(false)
const cursorStyle = ref('auto')
const {width, height} = toRefs(chartEditStore.getEditCanvasConfig)
const startX = ref(0)
const startY = ref(0)
const lines = reactive({h: [], v: []})

const {getEditCanvasConfig, getEditCanvas} = toRefs(chartEditStore)

// 锚点
const pointList = ['t', 'r', 'b', 'l', 'lt', 'rt', 'lb', 'rb']

// 光标朝向
const cursorResize = ['n', 'e', 's', 'w', 'nw', 'ne', 'sw', 'se']

const collapsed1 = ref<boolean>(getDetails.value)
const collapsed2 = ref<boolean>(getDetails.value)

// 颜色
const themeColor = computed(() => {
  return designStore.getAppTheme
})

// 计算当前选中目标
const hover = (item: PropType<CreateComponentType | CreateComponentGroupType>) => {
  const isDrag = chartEditStore.getEditCanvas[EditCanvasTypeEnum.IS_DRAG]
  if (isDrag) return false

  if (item.status.lock) return false
  return item.id === chartEditStore.getTargetChart.hoverId
}

// 兼容多值场景
const select = (item: PropType<CreateComponentType | CreateComponentGroupType>) => {
  const id = item.id
  if (item.status.lock) return false
  return chartEditStore.getTargetChart.selectId.find((e: string) => e === id)
}

// 锁定
const lock = (item: PropType<CreateComponentType | CreateComponentGroupType>) => {
  return item.status.lock
}

// 隐藏
const hide = (item: PropType<CreateComponentType | CreateComponentGroupType>) => {
  return item.status.hide
}

const size = computed(() => {
  return {
    w: getEditCanvasConfig.value.width,
    h: getEditCanvasConfig.value.height
  }
})

// 背景
const rangeStyle2 = computed(() => {
  // 设置背景色和图片背景
  const background = chartEditStore.getEditCanvasConfig.background
  const backgroundImage = chartEditStore.getEditCanvasConfig.backgroundImage
  const selectColor = chartEditStore.getEditCanvasConfig.selectColor
  const backgroundColor = background ? background : undefined

  const computedBackground = selectColor
    ? {background: backgroundColor}
    : {background: `url(${backgroundImage}) no-repeat center center / cover !important`}

  // @ts-ignore
  return {
    ...computedBackground,
    width: 'inherit',
    height: 'inherit'
  }
})

const collapsedHandle1 = () => {
  collapsed1.value = true
  setItem(ChartLayoutStoreEnum.DETAILS, true)
}

const expandHandle1 = () => {
  collapsed1.value = false
  setItem(ChartLayoutStoreEnum.DETAILS, false)
}

const collapsedHandle2 = () => {
  collapsed2.value = true
  setItem(ChartLayoutStoreEnum.DETAILS, true)
}

const expandHandle2 = () => {
  collapsed2.value = false
  setItem(ChartLayoutStoreEnum.DETAILS, false)
}

const rangeStyle = computed(() => {
  // 缩放
  const scale = {
    transform: `scale(${getEditCanvas.value.scale})`
  }
  // @ts-ignore
  return {...useSizeStyle(size.value), ...scale}
})

const scale = computed(() => {
  return chartEditStore.getEditCanvas.scale
})

// 滚动条拖动的宽度
const containerWidth = computed(() => {
  return `${window.innerWidth * 2}px`
})

// 滚动条拖动的高度
const containerHeight = computed(() => {
  return `${height.value * 2}px`
})

// 主题
const paletteStyle = computed(() => {
  const isDarkTheme = designStore.getDarkTheme
  return isDarkTheme
    ? {
      bgColor: '#18181c',
      longfgColor: '#4d4d4d',
      shortfgColor: '#4d4d4d',
      fontColor: '#4d4d4d',
      shadowColor: '#18181c',
      borderColor: '#18181c',
      cornerActiveColor: '#18181c'
    }
    : {}
})

// 主题色
const themeSetting = computed(() => {
  const chartThemeSetting = chartEditStore.getEditCanvasConfig.chartThemeSetting
  return chartThemeSetting
})

// 处理鼠标拖动
const handleWheel = (e: any) => {
  if (e.ctrlKey || e.metaKey) {
    e.preventDefault()
    let resScale = scale.value
    // 放大(200%)
    if (e.wheelDelta >= 0 && scale.value < 2) {
      resScale = scale.value + 0.05
      chartEditStore.setScale(resScale)
      return
    }
    // 缩小(10%)
    if (e.wheelDelta < 0 && scale.value > 0.1) {
      resScale = scale.value - 0.05
      chartEditStore.setScale(resScale)
    }
  }
}

// 拖拽处理
const dragStartHandle = (e: DragEvent, item: ConfigType) => {
  if (item.disabled) return
  // 动态注册图表组件
  componentInstall(item.chartKey, fetchChartComponent(item))
  componentInstall(item.conKey, fetchConfigComponent(item))
  // 将配置项绑定到拖拽属性上
  e!.dataTransfer!.setData(DragKeyEnum.DRAG_KEY, JSONStringify(omit(item, ['image'])))
  // 修改状态
  chartEditStore.setEditCanvas(EditCanvasTypeEnum.IS_CREATE, true)
}

// 拖拽结束
const dragendHandle = () => {
  chartEditStore.setEditCanvas(EditCanvasTypeEnum.IS_CREATE, false)
}

// 双击添加
const dblclickHandle = async (item: ConfigType) => {
  if (item.disabled) return
  try {
    // 动态注册图表组件
    componentInstall(item.chartKey, fetchChartComponent(item))
    componentInstall(item.conKey, fetchConfigComponent(item))
    // 创建新图表组件
    let newComponent: CreateComponentType = await createComponent(item)
    if (item.redirectComponent) {
      item.dataset && (newComponent.option.dataset = item.dataset)
      newComponent.chartConfig.title = item.title
      newComponent.chartConfig.chartFrame = item.chartFrame
    }
    // 添加
    chartEditStore.addComponentList(newComponent, false, true)
    // 选中
    chartEditStore.setTargetSelectChart(newComponent.id)

  } catch (error) {
    console.error(error)

    window['$message'].warning(`图表正在研发中, 敬请期待...`)
  }
}

// 单击事件
const clickHandle = (item: ConfigType) => {
  item?.configEvents?.addHandle(item)
}

const deleteHandle = (item: ConfigType, index: number) => {
  goDialog({
    message: '是否删除此图片？',
    transformOrigin: 'center',
    onPositiveCallback: () => {
      const packagesStore = usePackagesStore()
      emit('deletePhoto', item, index)
      packagesStore.deletePhotos(item, index)
    }
  })
}

// 滚动条处理
const handleScroll = () => {
  if (!$app.value) return
  const screensRect = $app.value.getBoundingClientRect()
  const canvasRect = refSketchRuleBox.value.getBoundingClientRect()
  // 标尺开始的刻度
  startX.value = (screensRect.left + thick - canvasRect.left) / scale.value
  startY.value = (screensRect.top + thick - canvasRect.top) / scale.value
}

// 拖拽处理
const dragCanvas = (e: any) => {
  e.preventDefault()
  e.stopPropagation()

  if (e.which == 2) isPressSpace.value = true
  else if (!window.$KeyboardActive?.space) return
  // @ts-ignore
  document.activeElement?.blur()

  const startX = e.pageX
  const startY = e.pageY

  const listenMousemove = listen(window, 'mousemove', (e: any) => {
    const nx = e.pageX - startX
    const ny = e.pageY - startY

    const [prevMoveX1, prevMoveX2] = prevMoveXValue
    const [prevMoveY1, prevMoveY2] = prevMoveYValue

    prevMoveXValue = [prevMoveX2, nx]
    prevMoveYValue = [prevMoveY2, ny]

    $app.value.scrollLeft -=
      prevMoveX2 > prevMoveX1 ? Math.abs(prevMoveX2 - prevMoveX1) : -Math.abs(prevMoveX2 - prevMoveX1)
    $app.value.scrollTop -=
      prevMoveY2 > prevMoveY1 ? Math.abs(prevMoveY2 - prevMoveY1) : -Math.abs(prevMoveY2 - prevMoveY1)
  })

  const listenMouseup = listen(window, 'mouseup', () => {
    listenMousemove()
    listenMouseup()
    prevMoveXValue = [0, 0]
    prevMoveYValue = [0, 0]
    isPressSpace.value = false
  })
}

// 计算画布大小
const canvasBox = () => {
  const layoutDom = document.getElementById('iot-chart-edit-layout')
  if (layoutDom) {
    // 此处减去滚动条的宽度和高度
    const scrollW = 20
    return {
      height: layoutDom.clientHeight - scrollW,
      width: layoutDom.clientWidth - scrollW
    }
  }
  return {
    width: width.value,
    height: height.value
  }
}

// 重绘标尺
const reDraw = throttle(() => {
  sketchRuleReDraw.value = false
  setTimeout(() => {
    sketchRuleReDraw.value = true
  }, 10)
}, 20)

// 滚动居中
const canvasPosCenter = () => {
  const {width: containerWidth, height: containerHeight} = $container.value.getBoundingClientRect()
  const {width, height} = canvasBox()

  $app.value.scrollLeft = containerWidth / 2 - width / 2
  $app.value.scrollTop = containerHeight / 2 - height / 2
}

// 模态层
const rangeModelStyle = computed(() => {
  const dragStyle = getEditCanvas.value.isCreate && {'z-index': 99999}
  // @ts-ignore
  return {...useSizeStyle(size.value), ...dragStyle}
})

const useSizeStyle = (attr: AttrType, scale?: number) => {
  if (!attr) return {}
  return {
    width: `${scale ? scale * attr.w : attr.w}px`,
    height: `${scale ? scale * attr.h : attr.h}px`
  }
}

const props = defineProps({
  menuOptions: {
    type: Array as PropType<ConfigType[]>,
    default: () => []
  },
  selectOptions: {
    type: Object,
    default: () => {
    }
  },
  item: {
    type: Object as PropType<CreateComponentType | CreateComponentGroupType>,
    required: true
  },
  hiddenPoint: {
    type: Boolean,
    required: false
  }
})

let packages = reactive<{
  [T: string]: any
}>({
  // 侧边栏
  menuOptions: [],
  // 当前选择
  selectOptions: {},
  // 分类归档
  categorys: {
    all: []
  },
  categoryNames: {
    all: '所有'
  },
  // 分类归档数量
  categorysNum: 0,
  // 存储不同类别组件进来的选中值
  saveSelectOptions: {}
})

const selectValue = ref<string>('all')

// 设置初始列表
const setSelectOptions = (categorys: any) => {
  for (const val in categorys) {
    packages.selectOptions = categorys[val]
    break
  }
}

// 页面对组件发生点击事件后，获取该组件数据（页面监听事件）
watch(
  // @ts-ignore
  () => props.selectOptions,
  (newData: { list: ConfigType[] }) => {
    packages.categorysNum = 0
    if (!newData) return
    newData.list.forEach((e: ConfigType) => {
      const value: ConfigType[] = (packages.categorys as any)[e.category]
      packages.categorys[e.category] = value && value.length ? [...value, e] : [e]
      packages.categoryNames[e.category] = e.categoryName
      packages.categorys['all'].push(e)
    })
    for (const val in packages.categorys) {
      packages.categorysNum += 1
      packages.menuOptions.push({
        key: val,
        label: packages.categoryNames[val]
      })
    }
    setSelectOptions(packages.categorys)
    // 默认选中处理
    selectValue.value = packages.menuOptions[0]['key']
  },
  {
    immediate: true
  }
)

// 处理主题变化
watch(
  () => designStore.getDarkTheme,
  () => {
    reDraw()
  }
)

// 页面面板折叠/展开
watch(getDetails, newData => {
  if (newData) {
    collapsedHandle()
  } else {
    expandHandle()
  }
})

// 处理标尺重制大小
watch(
  () => scale.value,
  (newValue, oldValue) => {
    if (oldValue !== newValue && chartLayoutStore.getRePositionCanvas) {
      chartLayoutStore.setItemUnHandle(ChartLayoutStoreEnum.RE_POSITION_CANVAS, false)
    }
    handleScroll()
    setTimeout(() => {
      canvasPosCenter()
      reDraw()
    }, 400)
  }
)

// 处理鼠标样式
watch(
  () => isPressSpace.value,
  newValue => {
    cursorStyle.value = newValue ? 'grab' : 'auto'
  }
)

onMounted(() => {
  if ($app.value) {
    $app.value.addEventListener('wheel', handleWheel, {passive: false})
    canvasPosCenter()
  }
})

// 键盘事件
onMounted(() => {
  useAddKeyboard()
})

onUnmounted(() => {
  if ($app.value) {
    $app.value.removeEventListener('wheel', handleWheel)
  }
})

window.onKeySpacePressHold = (isHold: boolean) => {
  isPressSpace.value = isHold
}
</script>

<style>
/* 使用 SCSS 会报错，直接使用最基础的 CSS 进行修改，
此库有计划 Vue3 版本，但是开发的时候还没发布 */
#mb-ruler {
  top: 0;
  left: 0;
}

/* 横线 */
#mb-ruler .v-container .lines .line {
  /* 最大缩放 200% */
  width: 200vw !important;
  border-top: 1px dashed v-bind('themeColor') !important;
}

#mb-ruler .v-container .indicator {
  border-bottom: 1px dashed v-bind('themeColor') !important;
}

/* 竖线 */
#mb-ruler .h-container .lines .line {
  /* 最大缩放 200% */
  height: 200vh !important;
  border-left: 1px dashed v-bind('themeColor') !important;
}

#mb-ruler .h-container .indicator {
  border-left: 1px dashed v-bind('themeColor') !important;
}

/* 坐标数值背景颜色 */
#mb-ruler .indicator .value {
  background-color: rgba(0, 0, 0, 0);
}

/* 删除按钮 */
#mb-ruler .line .del {
  padding: 0;
  color: v-bind('themeColor');
  font-size: 26px;
  font-weight: bolder;
}

#mb-ruler .corner {
  border-width: 0 !important;
}
</style>

<style lang="less" scoped>
.app-container {
  overflow: hidden;
  display: flex;

  .left-side {
    width: 350px !important;

    .iot-content-charts-item-box {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 9px;
      transition: all 0.7s linear;
      width: 180px;

      .item-box {
        position: relative;
        margin: 0;
        width: 100%;
        overflow: hidden;
        border-radius: 6px;
        cursor: pointer;
        border: 1px solid rgba(0, 0, 0, 0);
        background-color: #232324;

        .list-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 2px 15px;
          background-color: #2a2a2b;

          .text {
            color: rgba(255, 255, 255, 0.52);
            font-size: 12px;
            margin-left: 8px;
            user-select: none;
          }
        }

        .list-center {
          padding: 6px 0;
          height: 100px;
          overflow: hidden;
          display: flex;
          justify-content: center;
          align-items: center;
          text-align: center;

          .list-img {
            height: 100px;
            max-width: 140px;
            border-radius: 6px;
            object-fit: contain;
            transition: all 0.4s;
          }
        }

        .list-bottom {
          display: none;

          .list-bottom-text {
            font-size: 12px;
            padding-left: 5px;
          }
        }

        .list-model {
          z-index: 1;
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background-color: rgba(0, 0, 0, 0);
        }

        .list-tools {
          position: absolute;
          display: flex;
          justify-content: center;
          align-items: center;
          bottom: 0;
          left: 0;
          margin: 0 4px 2px;
          height: 26px;
          width: calc(100% - 8px);
          opacity: 0;
          border-radius: 6px;
          backdrop-filter: blur(20px);
          background-color: rgba(255, 255, 255, 0.15);

          &:hover {
            background-color: rgba(232, 128, 128, 0.7);
          }
        }
      }
    }
  }

  .iot-content-box {
    height: calc(100vh - @header-height);
    margin: 1px;
    margin-bottom: 0;
    background-color: #fafafc;
    background-image: linear-gradient(#fafafc 14px, transparent 0), linear-gradient(90deg, transparent 14px, #373739 0);
    background-size: 15px 15px, 15px 15px;
    position: relative;
    z-index: auto;
    flex: auto;
    overflow: hidden;

    .iot-sketch-rule {
      overflow: hidden;
      width: 100%;
      height: 100%;

      .edit-screens {
        position: absolute;
        width: 100%;
        height: 100%;
        overflow: auto;
        user-select: none;
        padding-bottom: 0px;

        /* firefox */
        scrollbar-color: rgba(144, 146, 152, 0.3) transparent;
        scrollbar-width: thin;

        /* chrome */

        &::-webkit-scrollbar,
        &::-webkit-scrollbar-track-piece {
          background-color: transparent;
        }

        &::-webkit-scrollbar {
          width: 7px;
        }

        &::-webkit-scrollbar-thumb {
          border-radius: 5px;
          background-color: rgba(144, 146, 152, 0.3);
        }

        // 修复右下角白点用的
        &::-webkit-scrollbar-corner {
          background-color: transparent;
        }
      }

      .fix-edit-screens-block {
        position: absolute;
        bottom: 0;
        right: 0;
        width: 10px;
        height: 10px;
        background-color: @color-dark-bg-1;
      }

      .edit-screen-container {
        position: absolute;
        height: v-bind('containerHeight');
        top: 0;
        left: 0;
      }

      .canvas {
        position: absolute;
        top: 60%;
        left: 50%;
        transform-origin: 50% 0;
        transform: translateY(-50%);

        &:hover {
          cursor: v-bind('cursorStyle');
        }

        &:active {
          cursor: crosshair;
        }

        #iot-chart-edit-content {

          .iot-edit-range {
            position: relative;
            transform-origin: left top;
            background-size: cover;
            overflow: hidden;
            background-color: @filter-color-login-light;
            border-color: @filter-color-login-light-shallow;
            transition: all 0.4s;

            .iot-edit-range-model {
              z-index: -1;
              position: absolute;
              left: 0;
              top: 0;
            }

            .iot-shape-box {
              position: absolute;
              cursor: move;

              &.lock {
                cursor: default !important;
              }

              &.hide {
                display: none;
              }

              /* 锚点 */

              .shape-point {
                z-index: 1;
                position: absolute;
                width: 7px;
                height: 7px;
                border: 3px solid v-bind('themeColor');
                border-radius: 5px;
                background-color: #fff;
                transform: translate(-40%, -30%);

                &.t {
                  width: 30px;
                  transform: translate(-50%, -50%);
                }

                &.b {
                  width: 30px;
                  transform: translate(-50%, -30%);
                }

                &.l,
                &.r {
                  height: 30px;
                }

                &.r {
                  transform: translate(-20%, -50%);
                }

                &.l {
                  transform: translate(-45%, -50%);
                }

                &.rt,
                &.rb {
                  transform: translate(-30%, -30%);
                }
              }

              /* 选中 */

              .shape-modal {
                position: absolute;
                top: 0;
                left: 0;

                .shape-modal-select,
                .shape-modal-change {
                  position: absolute;
                  width: 100%;
                  height: 100%;
                  border-radius: 4px;
                }

                .shape-modal-select {
                  opacity: 0.1;
                  top: 2px;
                  left: 2px;

                  &.active {
                    background-color: v-bind('themeColor');
                  }
                }

                .shape-modal-change {
                  border: 2px solid rgba(0, 0, 0, 0);

                  &.selectActive,
                  &.hoverActive {
                    border-color: v-bind('themeColor');
                    border-width: 2px;
                  }

                  &.hoverActive {
                    border-style: dotted;
                  }

                  &.selectActive {
                    border-style: solid;
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

</style>
