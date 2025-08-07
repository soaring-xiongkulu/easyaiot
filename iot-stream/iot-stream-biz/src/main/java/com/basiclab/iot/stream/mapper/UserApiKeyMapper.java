package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.stream.storager.dto.UserApiKey;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Mapper
@Repository
public interface UserApiKeyMapper {

    /**
     * 添加用户API密钥
     *
     * @param userApiKey 用户API密钥实体
     * @return 插入结果
     */
    int add(UserApiKey userApiKey);

    /**
     * 更新用户API密钥信息
     *
     * @param userApiKey 用户API密钥实体
     * @return 更新结果
     */
    int update(UserApiKey userApiKey);

    /**
     * 启用用户API密钥
     *
     * @param id 用户API密钥ID
     * @return 更新结果
     */
    int enable(@Param("id") int id);

    /**
     * 禁用用户API密钥
     *
     * @param id 用户API密钥ID
     * @return 更新结果
     */
    int disable(@Param("id") int id);

    /**
     * 更新用户API密钥
     *
     * @param id       用户API密钥ID
     * @param apiKey   新的API密钥值
     * @return 更新结果
     */
    int apiKey(@Param("id") int id, @Param("apiKey") String apiKey);

    /**
     * 更新用户API密钥备注
     *
     * @param id       用户API密钥ID
     * @param remark   新的备注
     * @return 更新结果
     */
    int remark(@Param("id") int id, @Param("remark") String remark);

    /**
     * 删除用户API密钥
     *
     * @param id 用户API密钥ID
     * @return 删除结果
     */
    int delete(@Param("id") int id);

    /**
     * 根据ID查询用户API密钥
     *
     * @param id 用户API密钥ID
     * @return 用户API密钥实体
     */
    UserApiKey selectById(@Param("id") int id);

    /**
     * 根据API密钥查询用户API密钥
     *
     * @param apiKey API密钥值
     * @return 用户API密钥实体
     */
    UserApiKey selectByApiKey(@Param("apiKey") String apiKey);

    /**
     * 查询所有用户API密钥
     *
     * @return 用户API密钥列表
     */
    List<UserApiKey> selectAll();

    /**
     * 查询所有用户API密钥
     *
     * @return 用户API密钥列表
     */
    List<UserApiKey> getUserApiKeys();

    /**
     * 检查API密钥是否存在
     *
     * @param apiKey API密钥值
     * @return 是否存在
     */
    boolean isApiKeyExists(@Param("apiKey") String apiKey);
}