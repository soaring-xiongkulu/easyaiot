import {onMounted, onUnmounted, ref, toRefs} from 'vue'
import {useChartEditStore} from '@/store/modules/chartEditStore/chartEditStore'
import {EditCanvasTypeEnum} from '@/store/modules/chartEditStore/chartEditStore.d'
// 布局
// 布局
import {useChartLayoutStore} from '@/store/modules/chartLayoutStore/chartLayoutStore'
// 样式
import {useDesignStore} from '@/store/modules/designStore/designStore'

const chartEditStore = useChartEditStore()

// 布局处理
export const useLayout = (fn: () => Promise<void>) => {
  let removeScale: Function = () => {
  }
  onMounted(async () => {
    // 设置 Dom 值(ref 不生效先用 document)
    chartEditStore.setEditCanvas(
      EditCanvasTypeEnum.EDIT_LAYOUT_DOM,
      document.getElementById('iot-chart-edit-layout')
    )
    chartEditStore.setEditCanvas(
      EditCanvasTypeEnum.EDIT_CONTENT_DOM,
      document.getElementById('iot-chart-edit-content')
    )

    // 获取数据
    await fn()
    // 监听初始化
    removeScale = chartEditStore.listenerScale()

  })

  onUnmounted(() => {
    chartEditStore.setEditCanvas(EditCanvasTypeEnum.EDIT_LAYOUT_DOM, null)
    chartEditStore.setEditCanvas(EditCanvasTypeEnum.EDIT_CONTENT_DOM, null)
    removeScale()
  })
}

// 全局颜色
const designStore = useDesignStore()
const themeColor = ref(designStore.getAppTheme)

// 结构控制
const {setItem} = useChartLayoutStore()
const {getCharts} = toRefs(useChartLayoutStore())

export {
  themeColor,
  setItem,
  getCharts
}
