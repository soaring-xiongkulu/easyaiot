package com.basiclab.iot.node.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.node.domain.vo.NodeCephTopologyRespVO;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageMountCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageStackCheckRespVO;
import com.basiclab.iot.node.service.NodeStorageService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import com.basiclab.iot.node.domain.vo.NodeNfsClusterAssignReqVO;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "存储 - NFS 集群纳管")
@RestController
@RequestMapping("/node/storage/")
@Validated
@Slf4j
public class NodeStorageController {

    @Resource
    private NodeStorageService nodeStorageService;

    @GetMapping("/topology")
    @Operation(summary = "NFS 共享媒体节点拓扑")
    public CommonResult<NodeCephTopologyRespVO> topology() {
        return success(nodeStorageService.getCephTopology());
    }

    @PostMapping("/assign-nfs-cluster")
    @Operation(summary = "分配/切换 NFS 集群（服务端 + 客户端 tags）")
    public CommonResult<NodeCephTopologyRespVO> assignNfsCluster(@RequestBody NodeNfsClusterAssignReqVO req) {
        return success(nodeStorageService.assignNfsCluster(req));
    }

    @PostMapping("/check-ssh")
    @Operation(summary = "通过 SSH 检测 NFS 服务端 Export 与挂载状态")
    public CommonResult<NodeStorageStackCheckRespVO> checkBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeStorageService.checkStorageStackBySsh(nodeId));
    }

    @PostMapping("/check-mount-ssh")
    @Operation(summary = "通过 SSH 检测 CephFS 客户端挂载状态")
    public CommonResult<NodeStorageMountCheckRespVO> checkMountBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeStorageService.checkStorageMountBySsh(nodeId));
    }

    @PostMapping("/deploy-osd-ssh")
    @Operation(summary = "通过 SSH 在存储节点准备 Ceph OSD")
    public CommonResult<NodeMediaRemoteDeployRespVO> deployOsdBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeStorageService.deployStorageOsdBySsh(nodeId));
    }

    @PostMapping("/deploy-client-ssh")
    @Operation(summary = "通过 SSH 在目标节点挂载 CephFS 客户端")
    public CommonResult<NodeMediaRemoteDeployRespVO> deployClientBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeStorageService.deployStorageClientBySsh(nodeId));
    }

    @PostMapping("/deploy-pool-ssh")
    @Operation(summary = "通过 SSH 在 MON 节点创建 Ceph 存储池与 CephFS")
    public CommonResult<NodeMediaRemoteDeployRespVO> deployPoolBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeStorageService.deployStoragePoolBySsh(nodeId));
    }

    @PostMapping("/stop-osd-ssh")
    @Operation(summary = "通过 SSH 停止存储节点 OSD 服务")
    public CommonResult<NodeMediaRemoteDeployRespVO> stopOsdBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeStorageService.stopStorageOsdBySsh(nodeId));
    }

    @PostMapping("/unmount-ssh")
    @Operation(summary = "通过 SSH 卸载目标节点 CephFS 挂载")
    public CommonResult<NodeMediaRemoteDeployRespVO> unmountBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeStorageService.unmountStorageBySsh(nodeId));
    }

}
