package com.basiclab.iot.system.job.demo;

import com.basiclab.iot.common.core.context.TenantContextHolder;
import com.basiclab.iot.common.core.handler.JobHandler;
import com.basiclab.iot.common.core.job.TenantJob;
import com.basiclab.iot.system.dal.dataobject.user.AdminUserDO;
import com.basiclab.iot.system.dal.pgsql.user.AdminUserMapper;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import java.util.List;

/**
 * DemoJob
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Component
public class DemoJob implements JobHandler {

    @Resource
    private AdminUserMapper adminUserMapper;

    @Override
    @TenantJob // 标记多租户
    public String execute(String param) {
        System.out.println("当前租户：" + TenantContextHolder.getTenantId());
        List<AdminUserDO> users = adminUserMapper.selectList();
        return "用户数量：" + users.size();
    }

}
