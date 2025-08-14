import {ThemeEnum} from '../enums/appEnum'
import {LangEnum, PreviewScaleEnum} from '@/enums/styleEnum'
import {RequestHttpIntervalEnum} from '@/enums/httpEnum'

export const prefixCls = 'xingyuv'

export const multipleTabHeight = 30

export const darkMode = ThemeEnum.LIGHT

// 默认语言
export const lang = LangEnum.ZH

// 水印文字
export const watermarkText = "BasicLab基础架构实验室"

// 分组名称
export const groupTitle = "分组"

// 主题配置
export const theme = {
  // 默认是否开启深色主题
  darkTheme: false,
  //默认主题色
  appTheme: '#51d6a9',
  appThemeDetail: null,
}

// 图表初始配置(px)
export const chartInitConfig = {
  x: 50,
  y: 50,
  w: 500,
  h: 300,
  // 不建议动 offset
  offsetX: 0,
  offsetY: 0,
}

// dialog 图标的大小
export const dialogIconSize = '20'

// 侧边栏宽度
export const asideWidth = '270'

// 侧边栏折叠后的宽度，支持全部折叠会覆盖为 0
export const asideCollapsedWidth = 60

// 弹窗是否可以通过点击遮罩关闭
export const maskClosable = false

// 全局边框圆角
export const borderRadius = '4px'

// 轮播间隔
export const carouselInterval = 4000

// 工作台大屏背景图片大小限制（5M）
export const backgroundImageSize = 5

// 预览展示方式
export const previewScaleType = PreviewScaleEnum.FIT

// 编辑工作台同步到 JSON 的轮询间隔（5S）
export const editToJsonInterval = 5000

// 数据请求间隔
export const requestInterval = 30

// 数据请求间隔单位
export const requestIntervalUnit = RequestHttpIntervalEnum.SECOND

// 工作区域历史记录存储最大数量
export const editHistoryMax = 100

// 拖拽时蒙层的 z-index，需比所有图表高
export const canvasModelIndex = 9999

// 框选时蒙层的 z-index，需比所有图表高
export const selectBoxIndex = canvasModelIndex + 10

// app主题色预设
export const APP_PRESET_COLOR_LIST: string[] = [
  '#0960bd',
  '#0084f4',
  '#266CFBFF',
  '#536dfe',
  '#ff5c93',
  '#ee4f12',
  '#0096c7',
  '#9c27b0',
  '#ff9800',
]

// 顶部背景色预设
export const HEADER_PRESET_BG_COLOR_LIST: string[] = [
  '#ffffff',
  '#151515',
  '#266CFBFF',
  '#5172DC',
  '#018ffb',
  '#409eff',
  '#e74c3c',
  '#24292e',
  '#394664',
  '#001529',
  '#383f45',
]

// 左侧菜单背景色预设
export const SIDE_BAR_BG_COLOR_LIST: string[] = [
  '#001529',
  '#212121',
  '#273352',
  '#ffffff',
  '#191b24',
  '#191a23',
  '#304156',
  '#001628',
  '#28333E',
  '#344058',
  '#383f45',
]
