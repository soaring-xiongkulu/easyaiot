package com.basiclab.iot.system.api.user;

import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.util.ObjUtil;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.system.api.user.dto.AdminUserRespDTO;
import com.basiclab.iot.system.controller.admin.user.vo.user.UserSaveReqVO;
import com.basiclab.iot.system.dal.dataobject.dept.DeptDO;
import com.basiclab.iot.system.dal.dataobject.user.AdminUserDO;
import com.basiclab.iot.system.service.dept.DeptService;
import com.basiclab.iot.system.service.user.AdminUserService;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;

import static com.basiclab.iot.common.domain.CommonResult.success;
import static com.basiclab.iot.common.utils.collection.CollectionUtils.convertSet;

/**
 * AdminUserApiImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@RestController // 提供 RESTful API 接口，给 Feign 调用
@Validated
public class AdminUserApiImpl implements AdminUserApi {

    @Resource
    private AdminUserService userService;
    @Resource
    private DeptService deptService;

    @Override
    public CommonResult<AdminUserRespDTO> getUser(Long id) {
        AdminUserDO user = userService.getUser(id);
        return success(BeanUtils.toBean(user, AdminUserRespDTO.class));
    }

    @Override
    public CommonResult<Boolean> updateUserExperimentStatus(Long id, Integer doExperiment) {
        UserSaveReqVO userSaveReqVO = new UserSaveReqVO();
        userSaveReqVO.setId(id);
        userSaveReqVO.setDoExperiment(doExperiment);
        userService.updateUser(userSaveReqVO);
        return success(true);
    }

    @Override
    public CommonResult<Boolean> updateUserExperimentIntegral(Long id, Long integral) {
        AdminUserDO user = userService.getUser(id);
        integral = user.getIntegral() - integral;
        if (integral < 0) {
            return success(false);
        }
        UserSaveReqVO userSaveReqVO = new UserSaveReqVO();
        userSaveReqVO.setId(id);
        userSaveReqVO.setIntegral(integral);
        userService.updateUser(userSaveReqVO);
        return success(true);
    }

    @Override
    public CommonResult<List<AdminUserRespDTO>> getUserListBySubordinate(Long id) {
        // 1.1 获取用户负责的部门
        AdminUserDO user = userService.getUser(id);
        if (user == null) {
            return success(Collections.emptyList());
        }
        ArrayList<Long> deptIds = new ArrayList<>();
        DeptDO dept = deptService.getDept(user.getDeptId());
        if (dept == null) {
            return success(Collections.emptyList());
        }
        if (ObjUtil.notEqual(dept.getLeaderUserId(), id)) { // 校验为负责人
            return success(Collections.emptyList());
        }
        deptIds.add(dept.getId());
        // 1.2 获取所有子部门
        List<DeptDO> childDeptList = deptService.getChildDeptList(dept.getId());
        if (CollUtil.isNotEmpty(childDeptList)) {
            deptIds.addAll(convertSet(childDeptList, DeptDO::getId));
        }

        // 2. 获取部门对应的用户信息
        List<AdminUserDO> users = userService.getUserListByDeptIds(deptIds);
        users.removeIf(item -> ObjUtil.equal(item.getId(), id)); // 排除自己
        return success(BeanUtils.toBean(users, AdminUserRespDTO.class));
    }

    @Override
    public CommonResult<List<AdminUserRespDTO>> getUserList(Collection<Long> ids) {
        List<AdminUserDO> users = userService.getUserList(ids);
        return success(BeanUtils.toBean(users, AdminUserRespDTO.class));
    }

    @Override
    public CommonResult<List<AdminUserRespDTO>> getUserListByDeptIds(Collection<Long> deptIds) {
        List<AdminUserDO> users = userService.getUserListByDeptIds(deptIds);
        return success(BeanUtils.toBean(users, AdminUserRespDTO.class));
    }

    @Override
    public CommonResult<List<AdminUserRespDTO>> getUserListByPostIds(Collection<Long> postIds) {
        List<AdminUserDO> users = userService.getUserListByPostIds(postIds);
        return success(BeanUtils.toBean(users, AdminUserRespDTO.class));
    }

    @Override
    public CommonResult<Boolean> validateUserList(Collection<Long> ids) {
        userService.validateUserList(ids);
        return success(true);
    }

}
