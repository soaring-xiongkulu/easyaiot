package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.stream.bean.Group;
import com.basiclab.iot.stream.media.bean.MediaServer;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface MediaServerMapper extends BaseMapperX<MediaServer> {

    /**
     * 添加媒体服务器
     *
     * @param mediaServerItem 媒体服务器实体
     * @return 插入结果
     */
    int add(MediaServer mediaServerItem);

    /**
     * 更新媒体服务器信息
     *
     * @param mediaServerItem 媒体服务器实体
     * @return 更新结果
     */
    int update(MediaServer mediaServerItem);

    /**
     * 根据主机和端口更新媒体服务器信息
     *
     * @param mediaServerItem 媒体服务器实体
     * @return 更新结果
     */
    int updateByHostAndPort(MediaServer mediaServerItem);

    /**
     * 根据ID和服务器ID查询单个媒体服务器
     *
     * @param id       媒体服务器ID
     * @param serverId 服务器ID
     * @return 媒体服务器实体
     */
    MediaServer queryOne(@Param("id") String id, @Param("serverId") String serverId);

    /**
     * 根据服务器ID查询所有媒体服务器
     *
     * @param serverId 服务器ID
     * @return 媒体服务器列表
     */
    List<MediaServer> queryAll(@Param("serverId") String serverId);

    /**
     * 根据ID和服务器ID删除单个媒体服务器
     *
     * @param id       媒体服务器ID
     * @param serverId 服务器ID
     */
    void delOne(String id, @Param("serverId") String serverId);

    /**
     * 根据主机、端口和服务器ID查询单个媒体服务器
     *
     * @param host     主机地址
     * @param port     端口号
     * @param serverId 服务器ID
     * @return 媒体服务器实体
     */
    MediaServer queryOneByHostAndPort(@Param("host") String host, @Param("port") int port, @Param("serverId") String serverId);

    /**
     * 查询默认媒体服务器
     *
     * @param serverId 服务器ID
     * @return 默认媒体服务器实体
     */
    MediaServer queryDefault(@Param("serverId") String serverId);

    /**
     * 查询所有具有辅助端口的媒体服务器
     *
     * @param serverId 服务器ID
     * @return 具有辅助端口的媒体服务器列表
     */
    List<MediaServer> queryAllWithAssistPort(@Param("serverId") String serverId);
}