import type { ComponentPublicInstance, ComponentRenderProxy, FunctionalComponent, VNode, VNodeChild, PropType as VuePropType } from 'vue'

interface Window {
  $loading: any
  $message: any
  $dialog: any
  // 语言
  $t: any
  $vue: any
  // 键盘按键记录
  $KeyboardActive?: { [T: string]: boolean }
  onKeySpacePressHold?: Function

  // 编辑 JSON 的存储对象
  opener: any
}


declare global {
  const __APP_INFO__: {
    pkg: {
      name: string
      version: string
      dependencies: Recordable<string>
      devDependencies: Recordable<string>
    }
    lastBuildTime: string
  }
  // declare interface Window {
  //   // Global vue app instance
  //   __APP__: App<Element>;
  // }

  interface Document {
    mozFullScreenElement?: Element
    msFullscreenElement?: Element
    webkitFullscreenElement?: Element
  }

  // vue
  declare type PropType<T> = VuePropType<T>
  declare type VueNode = VNodeChild | JSX.Element

  export type Writable<T> = {
    -readonly [P in keyof T]: T[P]
  }

  declare type Nullable<T> = T | null
  declare type NonNullable<T> = T extends null | undefined ? never : T
  declare type Recordable<T = any> = Record<string, T>
  declare interface ReadonlyRecordable<T = any> {
    readonly [key: string]: T
  }
  declare interface Indexable<T = any> {
    [key: string]: T
  }
  declare type DeepPartial<T> = {
    [P in keyof T]?: DeepPartial<T[P]>
  }
  declare type TimeoutHandle = ReturnType<typeof setTimeout>
  declare type IntervalHandle = ReturnType<typeof setInterval>

  declare interface ChangeEvent extends Event {
    target: HTMLInputElement
  }

  declare interface WheelEvent {
    path?: EventTarget[]
  }
  interface ImportMetaEnv extends ViteEnv {
    __: unknown
  }

  declare interface ViteEnv {
    VITE_PORT: number
    VITE_USE_PWA: boolean
    VITE_PUBLIC_PATH: string
    VITE_PROXY: [string, string][]
    VITE_GLOB_APP_TITLE: string
    VITE_GLOB_APP_SHORT_NAME: string
    VITE_USE_CDN: boolean
    VITE_DROP_CONSOLE: boolean
    /** 开发时 Vite 是否用轮询监视文件（规避 inotify ENOSPC） */
    VITE_USE_POLLING: boolean
    VITE_BUILD_COMPRESS: 'gzip' | 'brotli' | 'none'
    VITE_BUILD_COMPRESS_DELETE_ORIGIN_FILE: boolean
    VITE_GENERATE_UI: string
    /** 天地图 API Key */
    VITE_TIANDITU_KEY: string
    /** 部署形态：mini | standard | full */
    VITE_GLOB_DEPLOY_PROFILE?: string
    /** 数据集批量上传最大并发数 */
    VITE_UPLOAD_MAX_CONCURRENCY?: string
    /** VISUALIZE 大屏编辑器基址 */
    VITE_GLOB_VISUALIZE_URL?: string
    /** FUXA 组态编辑器基址 */
    VITE_GLOB_FUXA_URL?: string
    /** EasyAIoT PANEL 运维控制台（留空则使用当前访问域名 + 9200 端口） */
    VITE_PANEL_URL?: string
  }

  declare function parseInt(s: string | number, radix?: number): number

  declare function parseFloat(string: string | number): number

  namespace JSX {
    // tslint:disable no-empty-interface
    type Element = VNode
    // tslint:disable no-empty-interface
    type ElementClass = ComponentRenderProxy
    interface ElementAttributesProperty {
      $props: any
    }
    interface IntrinsicElements {
      [elem: string]: any
    }
    interface IntrinsicAttributes {
      [elem: string]: any
    }
  }
}

declare module 'vue' {
  export type JSXComponent<Props = any> = { new (): ComponentPublicInstance<Props> } | FunctionalComponent<Props>
}
