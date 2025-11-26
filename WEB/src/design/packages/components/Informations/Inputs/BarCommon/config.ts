import {echartOptionProfixHandle, PublicConfigClass} from '@/design/packages/public'
import {BarCommonConfig} from './index'
import {CreateComponentType} from '@/design/packages/index.d'
import cloneDeep from 'lodash/cloneDeep'

export const includes = ['xAxis', 'yAxis', 'legend', 'grid']
export const seriesItem = {
  name: '2011',
  type: 'bar',
  data: [18203, 23489, 29034, 104970, 131744, 630230]
}
export const option = {
  title: {
    text: 'World111 Population'
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
  legend: {},
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'value',
    boundaryGap: [0, 0.01]
  },
  yAxis: {
    type: 'category',
    data: ['Brazil', 'Indonesia', 'USA', 'India', 'China', 'World']
  },
  series: [
    seriesItem, seriesItem
  ]
}

export default class Config extends PublicConfigClass implements CreateComponentType {
  public key = BarCommonConfig.key
  public chartConfig = cloneDeep(BarCommonConfig)
  // 图表配置项
  public option = echartOptionProfixHandle(option, includes)
}
