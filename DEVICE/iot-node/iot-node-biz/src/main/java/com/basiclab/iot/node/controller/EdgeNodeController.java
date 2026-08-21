package com.basiclab.iot.node.controller;

import com.basiclab.iot.common.core.aop.TenantIgnore;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.node.domain.vo.EdgeEnrollReqVO;
import com.basiclab.iot.node.domain.vo.EdgeEnrollRespVO;
import com.basiclab.iot.node.domain.vo.EdgeNodePageReqVO;
import com.basiclab.iot.node.domain.vo.EdgeNodeRespVO;
import com.basiclab.iot.node.domain.vo.EdgeNodeUpdateReqVO;
import com.basiclab.iot.node.domain.vo.EdgeRuntimeConfigReqVO;
import com.basiclab.iot.node.domain.vo.EdgeRuntimeConfigRespVO;
import com.basiclab.iot.node.service.EdgeNodeService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.validation.Valid;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "EDGE - 已废弃（改用 RUNTIME 原子模式 + MQTT 事件面）")
@RestController
@RequestMapping("/node/edge")
@Validated
@Slf4j
public class EdgeNodeController {

    @Resource
    private EdgeNodeService edgeNodeService;

    @PostMapping("/enroll")
    @Operation(summary = "[已废弃] EDGE 自助纳管 — 请改用 RUNTIME 原子模式")
    @TenantIgnore
    public CommonResult<EdgeEnrollRespVO> enroll(@Valid @RequestBody EdgeEnrollReqVO reqVO) {
        log.warn("[DEPRECATED] /node/edge/enroll：EDGE 模块已移除，请安装 RUNTIME 原子节点");
        return CommonResult.error(410, "EDGE 模块已移除：请使用 RUNTIME 原子模式（MQTT 告警 + HTTP 心跳）");
    }

    @PostMapping("/runtime-config")
    @Operation(summary = "[已废弃] EDGE 拉取动态运行时配置")
    @TenantIgnore
    public CommonResult<EdgeRuntimeConfigRespVO> runtimeConfig(@Valid @RequestBody EdgeRuntimeConfigReqVO reqVO) {
        log.warn("[DEPRECATED] /node/edge/runtime-config：EDGE 模块已移除");
        return CommonResult.error(410, "EDGE 模块已移除：运行时配置请通过 VIDEO/Agent 下发 RUNTIME ini 与 MQTT 环境变量");
    }

    @GetMapping("/page")
    @Operation(summary = "边缘节点分页（只读遗留；WEB 已隐藏）")
    public CommonResult<PageResult<EdgeNodeRespVO>> page(@Valid EdgeNodePageReqVO reqVO) {
        return success(edgeNodeService.getEdgeNodePage(reqVO));
    }

    @GetMapping("/get")
    @Operation(summary = "边缘节点详情（只读遗留）")
    @Parameter(name = "id", description = "edge_node.id", required = true)
    public CommonResult<EdgeNodeRespVO> get(@RequestParam("id") Long id) {
        return success(edgeNodeService.getEdgeNode(id));
    }

    @PutMapping("/update")
    @Operation(summary = "更新边缘节点（遗留）")
    public CommonResult<Boolean> update(@Valid @RequestBody EdgeNodeUpdateReqVO reqVO) {
        edgeNodeService.updateEdgeNode(reqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除边缘节点管理记录（遗留）")
    @Parameter(name = "id", description = "edge_node.id", required = true)
    public CommonResult<Boolean> delete(@RequestParam("id") Long id) {
        edgeNodeService.deleteEdgeNode(id);
        return success(true);
    }

}
