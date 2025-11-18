package com.basiclab.iot.system.api.dept;


import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.system.api.dept.dto.DeptRespDTO;
import com.basiclab.iot.system.dal.dataobject.dept.DeptDO;
import com.basiclab.iot.system.service.dept.DeptService;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import java.util.Collection;
import java.util.List;

import static com.basiclab.iot.common.domain.CommonResult.success;

/**
 * DeptApiImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@RestController // 提供 RESTful API 接口，给 Feign 调用
@Validated
public class DeptApiImpl implements DeptApi {

    @Resource
    private DeptService deptService;

    @Override
    public CommonResult<DeptRespDTO> getDept(Long id) {
        DeptDO dept = deptService.getDept(id);
        return success(BeanUtils.toBean(dept, DeptRespDTO.class));
    }

    @Override
    public CommonResult<List<DeptRespDTO>> getDeptList(Collection<Long> ids) {
        List<DeptDO> depts = deptService.getDeptList(ids);
        return success(BeanUtils.toBean(depts, DeptRespDTO.class));
    }

    @Override
    public CommonResult<Boolean> validateDeptList(Collection<Long> ids) {
        deptService.validateDeptList(ids);
        return success(true);
    }

    @Override
    public CommonResult<List<DeptRespDTO>> getChildDeptList(Long id) {
        List<DeptDO> depts = deptService.getChildDeptList(id);
        return success(BeanUtils.toBean(depts, DeptRespDTO.class));
    }

}
