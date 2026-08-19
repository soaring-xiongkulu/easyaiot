package com.basiclab.iot.node.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.node.domain.vo.ComputeNodePageReqVO;
import com.basiclab.iot.node.domain.vo.ComputeNodeRespVO;
import com.basiclab.iot.node.domain.vo.ComputeNodeSaveReqVO;
import com.basiclab.iot.node.domain.vo.NodeAgentCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodePortCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeMetricTrendReqVO;
import com.basiclab.iot.node.domain.vo.NodeMetricTrendRespVO;
import com.basiclab.iot.common.core.aop.TenantIgnore;
import com.basiclab.iot.node.domain.vo.PlatformAgentBootstrapRespVO;
import com.basiclab.iot.node.domain.vo.PlatformHostRespVO;
import com.basiclab.iot.node.service.ComputeNodeService;
import com.basiclab.iot.node.service.ControlPlaneEndpointResolver;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.validation.Valid;
import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "管理后台 - 服务器节点")
@RestController
@RequestMapping("/node/")
@Validated
@Slf4j
public class ComputeNodeController {

    @Resource
    private ComputeNodeService computeNodeService;
    @Resource
    private ControlPlaneEndpointResolver controlPlaneEndpointResolver;

    @PostMapping("/create")
    @Operation(summary = "创建服务器节点")
    public CommonResult<ComputeNodeRespVO> createNode(@Valid @RequestBody ComputeNodeSaveReqVO createReqVO) {
        return success(computeNodeService.createNode(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新服务器节点")
    public CommonResult<Boolean> updateNode(@Valid @RequestBody ComputeNodeSaveReqVO updateReqVO) {
        computeNodeService.updateNode(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除服务器节点")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<Boolean> deleteNode(@RequestParam("id") Long id) {
        computeNodeService.deleteNode(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得服务器节点")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<ComputeNodeRespVO> getNode(@RequestParam("id") Long id) {
        return success(computeNodeService.getNode(id));
    }

    @GetMapping("/page")
    @Operation(summary = "获得服务器节点分页")
    public CommonResult<PageResult<ComputeNodeRespVO>> getNodePage(@Valid ComputeNodePageReqVO pageReqVO) {
        return success(computeNodeService.getNodePage(pageReqVO));
    }

    @GetMapping("/metric-trend")
    @Operation(summary = "获得节点指标趋势（按节点分序列）")
    public CommonResult<NodeMetricTrendRespVO> getMetricTrend(@Valid NodeMetricTrendReqVO reqVO) {
        return success(computeNodeService.getMetricTrend(reqVO));
    }

    @PostMapping("/test-ssh")
    @Operation(summary = "测试 SSH 连通性")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<Boolean> testSsh(@RequestParam("id") Long id) {
        return success(computeNodeService.testSsh(id));
    }

    @PostMapping("/reset-agent-token")
    @Operation(summary = "重置 Agent 令牌")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<String> resetAgentToken(@RequestParam("id") Long id) {
        return success(computeNodeService.resetAgentToken(id));
    }

    @GetMapping("/agent-setup")
    @Operation(summary = "获取待纳管节点的 Agent 配置（含 Token）")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<ComputeNodeRespVO> getAgentSetup(@RequestParam("id") Long id) {
        return success(computeNodeService.getAgentSetup(id));
    }

    @GetMapping("/platform-host")
    @Operation(summary = "获取平台宿主机 IP（供 Agent 平台接入地址自动填充）")
    public CommonResult<PlatformHostRespVO> getPlatformHost() {
        return success(new PlatformHostRespVO(
                controlPlaneEndpointResolver.resolveHookHost(),
                controlPlaneEndpointResolver.resolveHookPort()));
    }

    @GetMapping("/platform-agent-bootstrap")
    @Operation(summary = "获取控制面宿主机 Agent 启动凭据（供宿主机自动拉起 Agent）")
    @TenantIgnore
    public CommonResult<PlatformAgentBootstrapRespVO> getPlatformAgentBootstrap() {
        return success(computeNodeService.getPlatformAgentBootstrap());
    }

    @PostMapping("/deploy-agent-ssh")
    @Operation(summary = "通过 SSH 自动部署 Agent")
    @Parameter(name = "nodeId", description = "节点编号", required = true)
    public CommonResult<NodeMediaRemoteDeployRespVO> deployAgentBySsh(
            @RequestParam("nodeId") Long nodeId,
            @RequestParam(value = "controlPlaneUrl", required = false) String controlPlaneUrl) {
        return success(computeNodeService.deployAgentBySsh(nodeId, controlPlaneUrl));
    }

    @PostMapping("/check-agent-ssh")
    @Operation(summary = "通过 SSH 检测 Agent 是否已部署")
    @Parameter(name = "nodeId", description = "节点编号", required = true)
    public CommonResult<NodeAgentCheckRespVO> checkAgentBySsh(
            @RequestParam("nodeId") Long nodeId,
            @RequestParam(value = "controlPlaneUrl", required = false) String controlPlaneUrl) {
        return success(computeNodeService.checkAgentBySsh(nodeId, controlPlaneUrl));
    }

    @PostMapping("/check-agent-port-ssh")
    @Operation(summary = "通过 SSH 检测 Agent 部署端口占用")
    @Parameter(name = "nodeId", description = "节点编号", required = true)
    public CommonResult<NodePortCheckRespVO> checkAgentPortBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(computeNodeService.checkAgentPortBySsh(nodeId));
    }

    @PostMapping("/stop-agent-ssh")
    @Operation(summary = "通过 SSH 停止 Agent 服务")
    @Parameter(name = "nodeId", description = "节点编号", required = true)
    public CommonResult<NodeMediaRemoteDeployRespVO> stopAgentBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(computeNodeService.stopAgentBySsh(nodeId));
    }

    @PostMapping("/remove-agent-ssh")
    @Operation(summary = "通过 SSH 删除 Agent 服务及安装目录")
    @Parameter(name = "nodeId", description = "节点编号", required = true)
    public CommonResult<NodeMediaRemoteDeployRespVO> removeAgentBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(computeNodeService.removeAgentBySsh(nodeId));
    }

    @PostMapping("/maintenance")
    @Operation(summary = "设置维护模式")
    public CommonResult<Boolean> setMaintenance(@RequestParam("id") Long id,
                                                @RequestParam("enabled") boolean enabled) {
        computeNodeService.setMaintenance(id, enabled);
        return success(true);
    }

}
