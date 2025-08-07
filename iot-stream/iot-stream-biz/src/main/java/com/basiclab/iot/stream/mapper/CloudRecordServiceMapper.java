package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.stream.media.bean.MediaServer;
import com.basiclab.iot.stream.service.bean.CloudRecordItem;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Set;

@Mapper
public interface CloudRecordServiceMapper extends BaseMapperX<CloudRecordItem> {

    /**
     * 添加云记录项
     *
     * @param cloudRecordItem 云记录项实体
     * @return 插入结果
     */
    int add(CloudRecordItem cloudRecordItem);

    /**
     * 获取云记录列表
     *
     * @param query 查询条件
     * @param app 应用名称
     * @param stream 流名称
     * @param startTimeStamp 开始时间戳
     * @param endTimeStamp 结束时间戳
     * @param callId 呼叫ID
     * @param mediaServerItemList 媒体服务器列表
     * @param ids 记录ID列表
     * @param ascOrder 是否升序排列
     * @return 云记录列表
     */
    List<CloudRecordItem> getList(@Param("query") String query, @Param("app") String app, @Param("stream") String stream,
                                  @Param("startTimeStamp")Long startTimeStamp, @Param("endTimeStamp")Long endTimeStamp,
                                  @Param("callId")String callId, List<MediaServer> mediaServerItemList,
                                  List<Integer> ids, @Param("ascOrder") Boolean ascOrder);

    /**
     * 查询云记录文件路径列表
     *
     * @param app 应用名称
     * @param stream 流名称
     * @param startTimeStamp 开始时间戳
     * @param endTimeStamp 结束时间戳
     * @param callId 呼叫ID
     * @param mediaServerItemList 媒体服务器列表
     * @return 文件路径列表
     */
    List<String> queryRecordFilePathList(@Param("app") String app, @Param("stream") String stream,
                                  @Param("startTimeStamp")Long startTimeStamp, @Param("endTimeStamp")Long endTimeStamp,
                                  @Param("callId")String callId, List<MediaServer> mediaServerItemList);

    /**
     * 更新云记录收集状态
     *
     * @param collect 收集状态
     * @param cloudRecordItemList 云记录项列表
     * @return 更新结果
     */
    int updateCollectList(@Param("collect") boolean collect, List<CloudRecordItem> cloudRecordItemList);

    /**
     * 根据文件路径列表和媒体服务器ID删除云记录
     *
     * @param filePathList 文件路径列表
     * @param mediaServerId 媒体服务器ID
     */
    void deleteByFileList(List<String> filePathList, @Param("mediaServerId") String mediaServerId);

    /**
     * 查询待删除的云记录列表
     *
     * @param endTimeStamp 结束时间戳
     * @param mediaServerId 媒体服务器ID
     * @return 待删除的云记录列表
     */
    List<CloudRecordItem> queryRecordListForDelete(@Param("endTimeStamp")Long endTimeStamp, String mediaServerId);

    /**
     * 修改指定ID的云记录收集状态
     *
     * @param collect 收集状态
     * @param recordId 云记录ID
     * @return 更新结果
     */
    int changeCollectById(@Param("collect") boolean collect, @Param("recordId") Integer recordId);

    /**
     * 根据ID列表删除云记录
     *
     * @param cloudRecordItemIdList 云记录ID列表
     * @return 删除结果
     */
    int deleteList(List<CloudRecordItem> cloudRecordItemIdList);

    /**
     * 根据呼叫ID查询云记录列表
     *
     * @param callId 呼叫ID
     * @return 云记录列表
     */
    List<CloudRecordItem> getListByCallId(@Param("callId") String callId);

    /**
     * 根据ID查询单个云记录
     *
     * @param id 云记录ID
     * @return 云记录实体
     */
    CloudRecordItem queryOne(@Param("id") Integer id);

    /**
     * 查询云记录对应的媒体服务器ID列表
     *
     * @param app 应用名称
     * @param stream 流名称
     * @param startTimeStamp 开始时间戳
     * @param endTimeStamp 结束时间戳
     * @return 媒体服务器ID列表
     */
    List<String> queryMediaServerId(@Param("app") String app,
                   @Param("stream") String stream,
                   @Param("startTimeStamp")Long startTimeStamp,
                   @Param("endTimeStamp")Long endTimeStamp);

    /**
     * 根据ID列表查询云记录
     *
     * @param ids 云记录ID列表
     * @return 云记录列表
     */
    List<CloudRecordItem> queryRecordByIds(Set<Integer> ids);
}