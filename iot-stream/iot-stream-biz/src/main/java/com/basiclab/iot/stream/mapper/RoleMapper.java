package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.stream.storager.dto.Role;
import org.apache.ibatis.annotations.Mapper;
import org.springframework.stereotype.Repository;

import java.util.List;

@Mapper
@Repository
public interface RoleMapper {

    /**
     * 添加角色
     *
     * @param role 角色实体
     * @return 插入结果
     */
    int add(Role role);

    /**
     * 更新角色信息
     *
     * @param role 角色实体
     * @return 更新结果
     */
    int update(Role role);

    /**
     * 删除角色
     *
     * @param id 角色ID
     * @return 删除结果
     */
    int delete(int id);

    /**
     * 根据ID查询角色
     *
     * @param id 角色ID
     * @return 角色实体
     */
    Role selectById(int id);

    /**
     * 查询所有角色
     *
     * @return 角色列表
     */
    List<Role> selectAll();
}