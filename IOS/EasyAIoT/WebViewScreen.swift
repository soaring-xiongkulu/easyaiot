import SwiftUI
import WebKit

/// 用系统 WebView 承载 APP 模块构建出的 H5 产物（www/ 目录）。
/// 资源通过自定义协议 easyiot://localhost/ 提供，页面以“正常网页”方式运行：
/// ES Module、localStorage、对后端 admin-api 的跨域请求均与真实部署一致
/// （后端网关已全量放开 CORS，见 DEVICE/iot-gateway/filter/cors/CorsFilter.java）。
struct WebViewScreen: UIViewRepresentable {
    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        // localStorage / token 等持久化在默认 DataStore 中，冷启动不丢登录态
        config.websiteDataStore = .`default`()
        config.setURLSchemeHandler(SchemeHandler(), forURLScheme: SchemeHandler.scheme)

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.isOpaque = false
        webView.backgroundColor = .white
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        if let url = URL(string: "\(SchemeHandler.scheme)://localhost/index.html") {
            webView.load(URLRequest(url: url))
        }
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}
}

/// 把壳工程内置 www/ 静态资源映射为 easyiot:// 虚拟主机。
final class SchemeHandler: NSObject, WKURLSchemeHandler {
    static let scheme = "easyiot"

    private static let mimeTypes: [String: String] = [
        "html": "text/html", "htm": "text/html",
        "js": "text/javascript", "mjs": "text/javascript",
        "css": "text/css", "json": "application/json", "map": "application/json",
        "wasm": "application/wasm",
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "gif": "image/gif", "svg": "image/svg+xml", "webp": "image/webp",
        "ico": "image/x-icon",
        "ttf": "font/ttf", "otf": "font/otf", "woff": "font/woff", "woff2": "font/woff2",
        "mp4": "video/mp4", "webm": "video/webm", "mp3": "audio/mpeg",
        "txt": "text/plain", "xml": "application/xml",
    ]

    /// 请求路径 → www/ 内相对路径；空路径落到 index.html，未命中回落到入口页兜底
    private func resolve(_ requestPath: String?) -> URL? {
        var rel = requestPath ?? "/"
        rel = removingPercentEncoding(rel)
        while rel.hasPrefix("/") { rel.removeFirst() }
        if rel.isEmpty || rel.hasSuffix("/") { rel += "index.html" }
        return Bundle.main.url(forResource: "www/\(rel)", withExtension: nil)
            ?? Bundle.main.url(forResource: "www/index.html", withExtension: nil)
    }

    private func mimeType(for path: String) -> String {
        let ext = (path as NSString).pathExtension.lowercased()
        return Self.mimeTypes[ext] ?? "application/octet-stream"
    }

    private func removingPercentEncoding(_ s: String) -> String {
        s.removingPercentEncoding ?? s
    }

    func webView(_ webView: WKWebView, start urlSchemeTask: WKURLSchemeTask) {
        guard let url = urlSchemeTask.request.url else {
            urlSchemeTask.didFailWithError(URLError(.badURL))
            return
        }
        guard let fileURL = resolve(url.path), let data = try? Data(contentsOf: fileURL) else {
            urlSchemeTask.didFailWithError(URLError(.fileDoesNotExist))
            return
        }
        let response = URLResponse(
            url: url,
            mimeType: mimeType(for: url.path),
            expectedContentLength: data.count,
            textEncodingName: nil
        )
        urlSchemeTask.didReceive(response)
        urlSchemeTask.didReceive(data)
        urlSchemeTask.didFinish()
    }

    func webView(_ webView: WKWebView, stop urlSchemeTask: WKURLSchemeTask) {
        // 同步读取内存响应，无异步任务需要取消
    }
}
