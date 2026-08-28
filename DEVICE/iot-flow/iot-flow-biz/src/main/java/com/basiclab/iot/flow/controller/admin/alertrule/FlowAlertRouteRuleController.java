package com.basiclab.iot.flow.controller.admin.alertrule;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.dal.dataobject.FlowAlertRouteRuleDO;
import com.basiclab.iot.flow.service.alertrule.FlowAlertRouteRuleService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import javax.validation.Valid;
import java.util.List;
import java.util.Map;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "管理后台 - FLOW 告警路由规则")
@RestController
@RequestMapping("/flow/alert-route-rule")
@Validated
public class FlowAlertRouteRuleController {

    @Resource
    private FlowAlertRouteRuleService routeRuleService;

    @PostMapping("/create")
    @Operation(summary = "创建路由规则")
    public CommonResult<Long> createRule(@Valid @RequestBody FlowAlertRouteRuleVO reqVO) {
        return success(routeRuleService.createRule(reqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新路由规则")
    public CommonResult<Boolean> updateRule(@Valid @RequestBody FlowAlertRouteRuleVO reqVO) {
        routeRuleService.updateRule(reqVO);
        return success(true);
    }

    @PutMapping("/update-enabled")
    @Operation(summary = "启用/停用路由规则")
    public CommonResult<Boolean> updateEnabled(@RequestBody FlowAlertRouteRuleVO reqVO) {
        routeRuleService.updateEnabled(reqVO.getId(), reqVO.getEnabled());
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除路由规则")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<Boolean> deleteRule(@RequestParam("id") Long id) {
        routeRuleService.deleteRule(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得路由规则")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<FlowAlertRouteRuleVO> getRule(@RequestParam("id") Long id) {
        return success(FlowAlertRouteRuleVO.of(routeRuleService.getRule(id)));
    }

    @GetMapping("/page")
    @Operation(summary = "获得路由规则分页")
    public CommonResult<PageResult<FlowAlertRouteRuleVO>> getRulePage(@Validated PageParam pageParam,
                                                                      @RequestParam(value = "ruleName", required = false) String ruleName,
                                                                      @RequestParam(value = "enabled", required = false) Boolean enabled) {
        PageResult<FlowAlertRouteRuleDO> page = routeRuleService.getRulePage(pageParam, ruleName, enabled);
        return success(new PageResult<>(page.getList().stream().map(FlowAlertRouteRuleVO::of).toList(), page.getTotal()));
    }

    @GetMapping("/list")
    @Operation(summary = "获得路由规则列表")
    public CommonResult<List<FlowAlertRouteRuleVO>> getRuleList(@RequestParam(value = "ruleName", required = false) String ruleName,
                                                                @RequestParam(value = "enabled", required = false) Boolean enabled) {
        PageParam noPage = new PageParam();
        noPage.setPageNo(1);
        noPage.setPageSize(PageParam.PAGE_SIZE_NONE);
        PageResult<FlowAlertRouteRuleDO> page = routeRuleService.getRulePage(noPage, ruleName, enabled);
        return success(page.getList().stream().map(FlowAlertRouteRuleVO::of).toList());
    }

    @PostMapping("/preview-match")
    @Operation(summary = "规则试匹配（传告警样例）")
    public CommonResult<FlowAlertRouteRuleVO> previewMatch(@RequestBody Map<String, Object> alertSnapshot) {
        FlowAlertRouteRuleDO matched = routeRuleService.previewMatch(alertSnapshot);
        return success(FlowAlertRouteRuleVO.of(matched));
    }

}
