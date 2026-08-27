import { webview } from '@kit.ArkWeb';
import { hilog } from '@kit.PerformanceAnalysisKit';

/**
 * EasyAIoT 壳页面。
 *
 * 用系统 ArkWeb 承载 APP 模块构建出的 H5 产物（resources/rawfile/www/ 目录）。
 * 不直接以 file:// 加载（Chromium 内核会拦截 file 源的 ES Module 与部分存储 API），
 * 而是把资源统一映射为虚拟主机 http://appassets.local，经 onInterceptRequest
 * 从 rawfile 同步取字节回填，页面因此以“正常网页”身份运行：
 * - ES Module / localStorage / 对后端网关的跨域请求与真实站点部署一致；
 * - 后端 CORS 已由 DEVICE/iot-gateway 的 CorsFilter 全量放开；
 * - 非 appassets.local 的请求（如视频流、外部链接）原样交还内核走真实网络。
 */
const BOOT_URL = 'http://appassets.local/index.html';

const MIME_TYPES: Record<string, string> = {
  'html': 'text/html',
  'htm': 'text/html',
  'js': 'text/javascript',
  'mjs': 'text/javascript',
  'css': 'text/css',
  'json': 'application/json',
  'map': 'application/json',
  'wasm': 'application/wasm',
  'png': 'image/png',
  'jpg': 'image/jpeg',
  'jpeg': 'image/jpeg',
  'gif': 'image/gif',
  'svg': 'image/svg+xml',
  'webp': 'image/webp',
  'ico': 'image/x-icon',
  'ttf': 'font/ttf',
  'otf': 'font/otf',
  'woff': 'font/woff',
  'woff2': 'font/woff2',
  'mp4': 'video/mp4',
  'webm': 'video/webm',
  'mp3': 'audio/mpeg',
  'txt': 'text/plain',
};

@Entry
@Component
struct Index {
  controller: webview.WebviewController = new webview.WebviewController();

  private mimeFor(name: string): string {
    const dot: number = name.lastIndexOf('.');
    const ext: string = dot >= 0 ? name.substring(dot + 1).toLowerCase() : '';
    return MIME_TYPES[ext] ?? 'application/octet-stream';
  }

  /** 从 rawfile 取出对应文件并构造 200 响应 */
  private respondOk(rawfilePath: string): WebResourceResponse {
    const context = getContext(this);
    const data: Uint8Array = context.resourceManager.getRawFileContentSync(rawfilePath);
    const response = new WebResourceResponse();
    response.setResponseCode(200);
    response.setReasonMessage('OK');
    response.setResponseEncoding('utf-8');
    response.setResponseMimeType(this.mimeFor(rawfilePath));
    response.setResponseData(data.buffer as ArrayBuffer);
    // H5 页面会跨域请求后端网关；与本方案 iOS 壳的处理保持一致
    response.setHeaderByName('Access-Control-Allow-Origin', '*', true);
    return response;
  }

  /** 空响应体 404 */
  private respondNotFound(): WebResourceResponse {
    const response = new WebResourceResponse();
    response.setResponseCode(404);
    response.setReasonMessage('Not Found');
    response.setResponseMimeType('text/plain');
    return response;
  }

  /** 把 appassets.local 的请求映射到 rawfile/www 下的同名文件 */
  private serveLocal(event?: { request: webview.WebResourceRequest }): WebResourceResponse {
    if (!event || !event.request) {
      return this.respondNotFound();
    }
    let path: string = event.request.getRequestUrl().replace(`${BOOT_URL}/`, '');
    // 截掉查询参数与锚点
    const queryAt: number = path.indexOf('?');
    if (queryAt >= 0) {
      path = path.substring(0, queryAt);
    }
    const hashAt: number = path.indexOf('#');
    if (hashAt >= 0) {
      path = path.substring(0, hashAt);
    }
    path = decodeURIComponent(path);
    while (path.startsWith('/')) {
      path = path.substring(1);
    }
    if (path.includes('..')) {
      return this.respondNotFound();
    }
    if (path.length === 0) {
      path = 'index.html';
    }
    const rawfilePath = `www/${path}`;
    try {
      return this.respondOk(rawfilePath);
    } catch (err) {
      // 未命中（刷新深层路由等）回落到入口页；SPA 为 hash 路由，极少触发
      hilog.warn(0x0000, 'EasyAIoT', 'rawfile miss: %{public}s', rawfilePath);
      try {
        return this.respondOk('www/index.html');
      } catch (e) {
        return this.respondNotFound();
      }
    }
  }

  build() {
    Column() {
      Web({ src: BOOT_URL, controller: this.controller })
        .javaScriptAccess(true)
        .domStorageAccess(true)
        .databaseAccess(true)
        .mixedMode(MixedMode.Compatibility)
        .zoomAccess(false)
        .width('100%')
        .height('100%')
        .backgroundColor(Color.White)
        .onInterceptRequest((event?: { request: webview.WebResourceRequest }) => this.serveLocal(event))
    }
    .width('100%')
    .height('100%')
  }
}
