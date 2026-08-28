package com.basiclab.iot.flow.controller.admin.group;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.dal.dataobject.FlowUserGroupDO;
import com.basiclab.iot.flow.service.group.FlowUserGroupService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.Data;
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
import javax.validation.constraints.NotEmpty;
import java.io.Serializable;
import java.util.List;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "管理后台 - FLOW 用户组")
@RestController
@RequestMapping("/flow/user-group")
@Validated
public class FlowUserGroupController {

    @Resource
    private FlowUserGroupService userGroupService;

    @PostMapping("/create")
    @Operation(summary = "创建用户组")
    public CommonResult<Long> createUserGroup(@Valid UserGroupReqVO reqVO) {
        return success(userGroupService.createUserGroup(reqVO.getName(), reqVO.getDescription(),
                reqVO.getMemberUserIds(), reqVO.getStatus()));
    }

    @PutMapping("/update")
    @Operation(summary = "更新用户组")
    public CommonResult<Boolean> updateUserGroup(@Valid UserGroupReqVO reqVO) {
        userGroupService.updateUserGroup(reqVO.getId(), reqVO.getName(), reqVO.getDescription(),
                reqVO.getMemberUserIds(), reqVO.getStatus());
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除用户组")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<Boolean> deleteUserGroup(@RequestParam("id") Long id) {
        userGroupService.deleteUserGroup(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得用户组")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<UserGroupReqVO> getUserGroup(@RequestParam("id") Long id) {
        FlowUserGroupDO group = userGroupService.getUserGroup(id);
        UserGroupReqVO vo = new UserGroupReqVO();
        vo.setId(group.getId());
        vo.setName(group.getName());
        vo.setDescription(group.getDescription());
        vo.setMemberUserIds(group.getMemberUserIds());
        vo.setStatus(group.getStatus());
        return success(vo);
    }

    @GetMapping("/page")
    @Operation(summary = "获得用户组分页")
    public CommonResult<PageResult<UserGroupReqVO>> getUserGroupPage(@Validated PageParam pageParam,
                                                                     @RequestParam(value = "name", required = false) String name,
                                                                     @RequestParam(value = "status", required = false) Integer status) {
        PageResult<FlowUserGroupDO> page = userGroupService.getUserGroupPage(pageParam, name, status);
        return success(new PageResult<>(page.getList().stream().map(this::toVO).toList(), page.getTotal()));
    }

    @GetMapping("/simple-list")
    @Operation(summary = "获得用户组精简列表")
    public CommonResult<List<UserGroupReqVO>> getUserGroupSimpleList() {
        return success(userGroupService.getUserGroupSimpleList().stream().map(this::toVO).toList());
    }

    private UserGroupReqVO toVO(FlowUserGroupDO group) {
        UserGroupReqVO vo = new UserGroupReqVO();
        vo.setId(group.getId());
        vo.setName(group.getName());
        vo.setDescription(group.getDescription());
        vo.setMemberUserIds(group.getMemberUserIds());
        vo.setStatus(group.getStatus());
        return vo;
    }

    @Schema(description = "管理后台 - 用户组 VO")
    @Data
    public static class UserGroupReqVO implements Serializable {

        private static final long serialVersionUID = 1L;

        private Long id;
        @NotEmpty(message = "用户组名称不能为空")
        private String name;
        private String description;
        private List<Long> memberUserIds;
        /** 状态：0 开启 / 1 禁用 */
        private Integer status;

    }

}
