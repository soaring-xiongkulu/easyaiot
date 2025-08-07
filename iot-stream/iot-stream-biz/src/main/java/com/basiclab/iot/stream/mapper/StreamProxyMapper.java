package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.stream.streamProxy.bean.StreamProxy;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Mapper
@Repository
public interface StreamProxyMapper {

    /**
     * 添加流代理
     *
     * @param streamProxyDto 流代理实体
     * @return 插入结果
     */
    int add(StreamProxy streamProxyDto);

    /**
     * 更新流代理信息
     *
     * @param streamProxyDto 流代理实体
     * @return 更新结果
     */
    int update(StreamProxy streamProxyDto);

    /**
     * 根据应用和流删除流代理
     *
     * @param app 应用标识
     * @param stream 流标识
     * @return 删除结果
     */
    int delByAppAndStream(String app, String stream);

    /**
     * 查询所有流代理
     *
     * @param query 查询条件
     * @param pulling 是否正在拉取
     * @param mediaServerId 媒体服务器ID
     * @return 流代理列表
     */
    List<StreamProxy> selectAll(@Param("query") String query, @Param("pulling") Boolean pulling, @Param("mediaServerId") String mediaServerId);

    /**
     * 根据应用和流查询单个流代理
     *
     * @param app 应用标识
     * @param stream 流标识
     * @return 流代理实体
     */
    StreamProxy selectOneByAppAndStream(@Param("app") String app, @Param("stream") String stream);

    /**
     * 查询指定媒体服务器中需要推送的流代理
     *
     * @param mediaServerId 媒体服务器ID
     * @param enable 是否启用
     * @return 流代理列表
     */
    List<StreamProxy> selectForPushingInMediaServer(@Param("mediaServerId") String mediaServerId, @Param("enable") boolean enable);

    /**
     * 获取所有流代理的数量
     *
     * @return 流代理数量
     */
    int getAllCount();

    /**
     * 获取正在拉取的流代理数量
     *
     * @return 正在拉取的流代理数量
     */
    int getOnline();

    /**
     * 根据ID删除流代理
     *
     * @param id 流代理ID
     * @return 删除结果
     */
    int delete(@Param("id") int id);

    /**
     * 根据ID列表删除流代理
     *
     * @param streamProxiesForRemove 流代理ID列表
     */
    void deleteByList(List<StreamProxy> streamProxiesForRemove);

    /**
     * 设置流代理为在线状态
     *
     * @param id 流代理ID
     * @return 更新结果
     */
    int online(@Param("id") int id);

    /**
     * 设置流代理为离线状态
     *
     * @param id 流代理ID
     * @return 更新结果
     */
    int offline(@Param("id") int id);

    /**
     * 根据ID查询流代理
     *
     * @param id 流代理ID
     * @return 流代理实体
     */
    StreamProxy select(@Param("id") int id);

    /**
     * 移除流代理的媒体服务器和流密钥
     *
     * @param id 流代理ID
     */
    void removeStream(@Param("id") int id);

    /**
     * 添加流代理的媒体服务器和流密钥
     *
     * @param streamProxy 流代理实体
     */
    void addStream(StreamProxy streamProxy);
}