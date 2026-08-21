package com.basiclab.iot.node.controller;

import com.basiclab.iot.common.core.aop.TenantIgnore;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.node.domain.vo.*;
import com.basiclab.iot.node.service.ControlPlaneService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.validation.Valid;
import java.util.List;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "管理后台 - 中心节点联邦")
@RestController
@RequestMapping("/node/control-plane/")
@Validated
@Slf4j
public class ControlPlaneController {

    private static final String PEER_TOKEN_HEADER = "X-Peer-Token";

    @Resource
    private ControlPlaneService controlPlaneService;

    @GetMapping("/lanes")
    @Operation(summary = "获取集群泳道（中心节点 + 工作节点）")
    public CommonResult<PageResult<ClusterLaneRespVO>> listLanes(@Valid ClusterLanePageReqVO reqVO) {
        return success(controlPlaneService.listLanes(reqVO));
    }

    @GetMapping("/peers")
    @Operation(summary = "获取对等中心节点列表")
    public CommonResult<List<ControlPlanePeerRespVO>> listPeers() {
        return success(controlPlaneService.listPeers());
    }

    @PostMapping("/peers/create")
    @Operation(summary = "添加对等中心节点并双向同步")
    public CommonResult<ControlPlanePeerRespVO> createPeer(@Valid @RequestBody ControlPlanePeerSaveReqVO reqVO) {
        return success(controlPlaneService.createPeer(reqVO));
    }

    @DeleteMapping("/peers/delete")
    @Operation(summary = "删除对等中心节点")
    @Parameter(name = "id", description = "对等中心节点编号", required = true)
    public CommonResult<Boolean> deletePeer(@RequestParam("id") Long id) {
        controlPlaneService.deletePeer(id);
        return success(true);
    }

    @PostMapping("/peers/sync")
    @Operation(summary = "手动同步对等中心节点")
    @Parameter(name = "id", description = "对等中心节点编号", required = true)
    public CommonResult<Boolean> syncPeer(@RequestParam("id") Long id) {
        controlPlaneService.syncPeer(id);
        return success(true);
    }

    @PostMapping("/lane/batch")
    @Operation(summary = "泳道工作节点批量操作")
    public CommonResult<Boolean> batchLaneAction(@Valid @RequestBody ClusterLaneBatchReqVO reqVO) {
        controlPlaneService.batchLaneAction(reqVO);
        return success(true);
    }

    @PostMapping("/peer/register")
    @Operation(summary = "对等中心节点互联注册（节点间调用）")
    @TenantIgnore
    public CommonResult<Boolean> registerPeer(
            @RequestHeader(value = PEER_TOKEN_HEADER, required = false) String inboundToken,
            @Valid @RequestBody ControlPlanePeerRegisterReqVO reqVO) {
        controlPlaneService.registerPeer(reqVO, inboundToken);
        return success(true);
    }

    @GetMapping("/snapshot")
    @Operation(summary = "本机中心节点快照（供对等节点拉取）")
    @TenantIgnore
    public CommonResult<ControlPlaneSnapshotRespVO> getSnapshot(
            @RequestHeader(value = PEER_TOKEN_HEADER, required = false) String inboundToken) {
        return success(controlPlaneService.getSnapshot(inboundToken));
    }

}
