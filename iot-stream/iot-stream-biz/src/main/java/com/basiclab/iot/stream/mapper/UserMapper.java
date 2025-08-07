package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.stream.storager.dto.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Mapper
@Repository
public interface UserMapper {

    /**
     * 添加用户
     *
     * @param user 用户实体
     * @return 插入结果
     */
    int add(User user);

    /**
     * 更新用户信息
     *
     * @param user 用户实体
     * @return 更新结果
     */
    int update(User user);

    /**
     * 删除用户
     *
     * @param id 用户ID
     * @return 删除结果
     */
    int delete(int id);

    /**
     * 根据用户名和密码查询用户
     *
     * @param username 用户名
     * @param password 密码
     * @return 用户实体
     */
    User select(@Param("username") String username, @Param("password") String password);

    /**
     * 根据ID查询用户
     *
     * @param id 用户ID
     * @return 用户实体
     */
    User selectById(int id);

    /**
     * 根据用户名查询用户
     *
     * @param username 用户名
     * @return 用户实体
     */
    User getUserByUsername(String username);

    /**
     * 查询所有用户
     *
     * @return 用户列表
     */
    List<User> selectAll();

    /**
     * 查询所有用户
     *
     * @return 用户列表
     */
    List<User> getUsers();

    /**
     * 更新用户的推送密钥
     *
     * @param id 用户ID
     * @param pushKey 新的推送密钥
     * @return 更新结果
     */
    int changePushKey(@Param("id") int id, @Param("pushKey") String pushKey);
}