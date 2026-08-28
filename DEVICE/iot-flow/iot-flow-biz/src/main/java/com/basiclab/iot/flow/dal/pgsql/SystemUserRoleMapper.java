package com.basiclab.iot.flow.dal.pgsql;

import com.baomidou.dynamic.datasource.annotation.DS;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

import java.util.Collection;
import java.util.List;

/**
 * system 库只读查询（候选人策略：角色 → 用户）
 *
 * yudao 系 RPC（RoleApi）只提供校验，无按角色查用户接口，故直查 system_user_role。
 */
@Mapper
@DS("system")
public interface SystemUserRoleMapper {

    @Select("<script>"
            + "SELECT DISTINCT ur.user_id FROM system_user_role ur"
            + " JOIN system_users u ON u.id = ur.user_id"
            + " WHERE ur.deleted = 0 AND u.deleted = 0 AND u.status = 0"
            + " AND ur.role_id IN <foreach collection='roleIds' item='rid' open='(' separator=',' close=')'>#{rid}</foreach>"
            + "</script>")
    List<Long> selectUserIdsByRoleIds(Collection<Long> roleIds);

}
