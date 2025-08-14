import type {App} from 'vue'
import {SketchRule} from 'vue3-sketch-ruler'

/**
 * 全局注册自定义组件
 * @param app
 */
export function setupCustomComponents(app: App) {
  app.component('SketchRule', SketchRule)
}
