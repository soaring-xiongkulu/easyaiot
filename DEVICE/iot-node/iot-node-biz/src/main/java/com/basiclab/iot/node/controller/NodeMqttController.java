package com.basiclab.iot.node.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodeMqttDeployReqVO;
import com.basiclab.iot.node.domain.vo.NodeMqttStackCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodePortCheckRespVO;
import com.basiclab.iot.node.service.NodeMqttService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.validation.Valid;
import java.util.Map;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "MQTT 网关 - EMQX 集群")
@RestController
@RequestMapping("/node/mqtt/")
@Validated
@Slf4j
public class NodeMqttController {

    @Resource
    private NodeMqttService nodeMqttService;

    @PostMapping("/deploy-stack")
    @Operation(summary = "在 MQTT 网关节点通过 Agent 部署 EMQX")
    public CommonResult<Map<String, Object>> deployStack(@Valid @RequestBody NodeMqttDeployReqVO reqVO) {
        return success(nodeMqttService.deployMqttStack(reqVO));
    }

    @PostMapping("/deploy-ssh")
    @Operation(summary = "通过 SSH 在 MQTT 网关节点自动部署 EMQX 集群")
    public CommonResult<NodeMediaRemoteDeployRespVO> deployBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeMqttService.deployMqttStackBySsh(nodeId));
    }

    @PostMapping("/check-ssh")
    @Operation(summary = "通过 SSH 检测 MQTT 网关节点 EMQX 是否已部署")
    public CommonResult<NodeMqttStackCheckRespVO> checkBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeMqttService.checkMqttStackBySsh(nodeId));
    }

    @PostMapping("/check-ports-ssh")
    @Operation(summary = "通过 SSH 检测 MQTT 网关部署端口占用")
    public CommonResult<NodePortCheckRespVO> checkPortsBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeMqttService.checkMqttPortsBySsh(nodeId));
    }

    @PostMapping("/stop-ssh")
    @Operation(summary = "通过 SSH 停止目标机 EMQX 服务")
    public CommonResult<NodeMediaRemoteDeployRespVO> stopBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeMqttService.stopMqttServiceBySsh(nodeId));
    }

    @PostMapping("/remove-container-ssh")
    @Operation(summary = "通过 SSH 删除目标机 EMQX 容器")
    public CommonResult<NodeMediaRemoteDeployRespVO> removeContainerBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeMqttService.removeMqttContainerBySsh(nodeId));
    }

    @PostMapping("/remove-image-ssh")
    @Operation(summary = "通过 SSH 删除目标机 EMQX Docker 镜像")
    public CommonResult<NodeMediaRemoteDeployRespVO> removeImageBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeMqttService.removeMqttImageBySsh(nodeId));
    }

}
