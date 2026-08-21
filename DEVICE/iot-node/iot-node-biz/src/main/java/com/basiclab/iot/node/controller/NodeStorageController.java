package com.basiclab.iot.node.controller;

import com.basiclab.iot.common.core.aop.TenantIgnore;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.node.domain.vo.NfsBridgeCreateReqVO;
import com.basiclab.iot.node.domain.vo.NfsClusterActivateReqVO;
import com.basiclab.iot.node.domain.vo.NfsMultiClusterOverviewRespVO;
import com.basiclab.iot.node.domain.vo.NodeCephTopologyRespVO;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodeNfsBatchRefreshReqVO;
import com.basiclab.iot.node.domain.vo.NodeNfsBatchRefreshRespVO;
import com.basiclab.iot.node.domain.vo.NodeNfsClusterAssignReqVO;
import com.basiclab.iot.node.domain.vo.NodeStorageFileDownloadResult;
import com.basiclab.iot.node.domain.vo.NodeStorageFileListRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageFileOpsRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageMountCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageOpLogPageReqVO;
import com.basiclab.iot.node.domain.vo.NodeStorageOpLogRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageStackCheckRespVO;
import com.basiclab.iot.node.service.NodeStorageService;
import com.basiclab.iot.node.service.NfsMultiClusterService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "存储 - NFS 集群纳管")
@RestController
@RequestMapping("/node/storage/")
@Validated
@Slf4j
public class NodeStorageController {

    @Resource
    private NodeStorageService nodeStorageService;
    @Resource
    private NfsMultiClusterService nfsMultiClusterService;

    @GetMapping("/topology")
    @Operation(summary = "NFS 共享媒体节点拓扑")
    public CommonResult<NodeCephTopologyRespVO> topology() {
        return success(nodeStorageService.getCephTopology());
    }

    @PostMapping("/assign-nfs-cluster")
    @Operation(summary = "分配/切换 NFS 集群（主/备服务端 + 客户端 tags）")
    public CommonResult<NodeCephTopologyRespVO> assignNfsCluster(@RequestBody NodeNfsClusterAssignReqVO req) {
        return success(nodeStorageService.assignNfsCluster(req));
    }

    @PostMapping("/promote-nfs-primary")
    @Operation(summary = "软 HA：升主 NFS 服务端（改 tags；客户端需重新挂载）")
    public CommonResult<NodeCephTopologyRespVO> promoteNfsPrimary(@RequestParam("nodeId") Long nodeId) {
        return success(nodeStorageService.promoteNfsPrimary(nodeId));
    }

    @TenantIgnore
    @GetMapping("/multi-cluster/overview")
    @Operation(summary = "NFS 多集群与桥接总览（泳道=集群）")
    public CommonResult<NfsMultiClusterOverviewRespVO> multiClusterOverview() {
        return success(nfsMultiClusterService.getOverview());
    }

    @TenantIgnore
    @PostMapping("/multi-cluster/activate")
    @Operation(summary = "切换生效主 NFS 集群（默认需先停桥接；forceStopBridges=true 可强制停）")
    public CommonResult<NfsMultiClusterOverviewRespVO> activateCluster(@RequestBody NfsClusterActivateReqVO req) {
        return success(nfsMultiClusterService.activateCluster(req));
    }

    @TenantIgnore
    @PostMapping("/multi-cluster/bridge/create")
    @Operation(summary = "创建主集群→从集群单向桥接（目标必须落在 _bridge/ 下）")
    public CommonResult<NfsMultiClusterOverviewRespVO> createBridge(@RequestBody NfsBridgeCreateReqVO req) {
        return success(nfsMultiClusterService.createBridge(req));
    }

    @TenantIgnore
    @PostMapping("/multi-cluster/bridge/stop")
    @Operation(summary = "停止桥接")
    public CommonResult<NfsMultiClusterOverviewRespVO> stopBridge(@RequestParam("bridgeId") Long bridgeId) {
        return success(nfsMultiClusterService.stopBridge(bridgeId));
    }

    @TenantIgnore
    @PostMapping("/multi-cluster/bridge/enable")
    @Operation(summary = "启用/停用桥接")
    public CommonResult<NfsMultiClusterOverviewRespVO> enableBridge(
            @RequestParam("bridgeId") Long bridgeId,
            @RequestParam("enabled") Boolean enabled) {
        return success(nfsMultiClusterService.enableBridge(bridgeId, Boolean.TRUE.equals(enabled)));
    }

    @TenantIgnore
    @PostMapping("/multi-cluster/bridge/run")
    @Operation(summary = "立即执行单向同步（首次全量含历史，后续增量；不覆盖客户业务目录）")
    public CommonResult<NfsMultiClusterOverviewRespVO> runBridge(@RequestParam("bridgeId") Long bridgeId) {
        return success(nfsMultiClusterService.runBridge(bridgeId));
    }

    @PostMapping("/batch-refresh-ssh")
    @Operation(summary = "批量 SSH 刷新 NFS 现状并落库")
    public CommonResult<NodeNfsBatchRefreshRespVO> batchRefreshBySsh(@RequestBody(required = false) NodeNfsBatchRefreshReqVO req) {
        return success(nodeStorageService.batchRefreshBySsh(req));
    }

    @GetMapping("/op-logs")
    @Operation(summary = "NFS 运维操作日志分页")
    public CommonResult<PageResult<NodeStorageOpLogRespVO>> opLogs(NodeStorageOpLogPageReqVO req) {
        return success(nodeStorageService.getOpLogPage(req));
    }

    @GetMapping("/files/list")
    @Operation(summary = "只读列出节点媒体挂载根目录")
    public CommonResult<NodeStorageFileListRespVO> listFiles(
            @RequestParam("nodeId") Long nodeId,
            @RequestParam(value = "path", required = false) String path) {
        return success(nodeStorageService.listMediaFiles(nodeId, path));
    }

    @GetMapping("/files/download")
    @Operation(summary = "下载节点媒体挂载根内文件（默认 ≤50MB）")
    public ResponseEntity<byte[]> downloadFile(
            @RequestParam("nodeId") Long nodeId,
            @RequestParam("path") String path) {
        NodeStorageFileDownloadResult file = nodeStorageService.downloadMediaFile(nodeId, path);
        String encoded = URLEncoder.encode(file.getFileName() != null ? file.getFileName() : "file",
                StandardCharsets.UTF_8).replace("+", "%20");
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename*=UTF-8''" + encoded)
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .contentLength(file.getContent() != null ? file.getContent().length : 0)
                .body(file.getContent());
    }

    @PostMapping("/files/mkdir")
    @Operation(summary = "在媒体挂载根内创建目录")
    public CommonResult<NodeStorageFileOpsRespVO> mkdir(
            @RequestParam("nodeId") Long nodeId,
            @RequestParam(value = "path", required = false) String path,
            @RequestParam("name") String name) {
        return success(nodeStorageService.mkdirMediaDir(nodeId, path, name));
    }

    @PostMapping(value = "/files/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary = "上传文件到媒体挂载根（默认 ≤50MB）")
    public CommonResult<NodeStorageFileOpsRespVO> upload(
            @RequestParam("nodeId") Long nodeId,
            @RequestParam(value = "path", required = false) String path,
            @RequestParam("file") MultipartFile file) {
        return success(nodeStorageService.uploadMediaFile(nodeId, path, file));
    }

    @PostMapping("/files/delete")
    @Operation(summary = "删除媒体挂载根内文件或目录（目录递归删除；禁止删根）")
    public CommonResult<NodeStorageFileOpsRespVO> deleteFile(
            @RequestParam("nodeId") Long nodeId,
            @RequestParam("path") String path) {
        return success(nodeStorageService.deleteMediaPath(nodeId, path));
    }

    @PostMapping("/files/rename")
    @Operation(summary = "重命名媒体挂载根内文件或目录（仅同目录改名）")
    public CommonResult<NodeStorageFileOpsRespVO> renameFile(
            @RequestParam("nodeId") Long nodeId,
            @RequestParam("path") String path,
            @RequestParam("newName") String newName) {
        return success(nodeStorageService.renameMediaPath(nodeId, path, newName));
    }

    @PostMapping("/check-ssh")
    @Operation(summary = "通过 SSH 检测 NFS 服务端 Export 与挂载状态")
    public CommonResult<NodeStorageStackCheckRespVO> checkBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeStorageService.checkStorageStackBySsh(nodeId));
    }

    @PostMapping("/check-mount-ssh")
    @Operation(summary = "通过 SSH 检测 NFS 客户端挂载状态")
    public CommonResult<NodeStorageMountCheckRespVO> checkMountBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeStorageService.checkStorageMountBySsh(nodeId));
    }

    @PostMapping("/deploy-osd-ssh")
    @Operation(summary = "通过 SSH 安装 NFS 服务端")
    public CommonResult<NodeMediaRemoteDeployRespVO> deployOsdBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeStorageService.deployStorageOsdBySsh(nodeId));
    }

    @PostMapping("/deploy-client-ssh")
    @Operation(summary = "通过 SSH 挂载 NFS 客户端")
    public CommonResult<NodeMediaRemoteDeployRespVO> deployClientBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeStorageService.deployStorageClientBySsh(nodeId));
    }

    @PostMapping("/deploy-pool-ssh")
    @Operation(summary = "通过 SSH 初始化 NFS Export")
    public CommonResult<NodeMediaRemoteDeployRespVO> deployPoolBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeStorageService.deployStoragePoolBySsh(nodeId));
    }

    @PostMapping("/stop-osd-ssh")
    @Operation(summary = "通过 SSH 停止 NFS 服务")
    public CommonResult<NodeMediaRemoteDeployRespVO> stopOsdBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeStorageService.stopStorageOsdBySsh(nodeId));
    }

    @PostMapping("/unmount-ssh")
    @Operation(summary = "通过 SSH 卸载 NFS 挂载")
    public CommonResult<NodeMediaRemoteDeployRespVO> unmountBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeStorageService.unmountStorageBySsh(nodeId));
    }

}
