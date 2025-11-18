package com.basiclab.iot.tdengine.service;


import com.basiclab.iot.device.domain.device.vo.TDDeviceDataResp;
import com.basiclab.iot.tdengine.domain.DeviceData;
import com.basiclab.iot.tdengine.domain.Fields;
import com.basiclab.iot.tdengine.domain.SelectDto;
import com.basiclab.iot.tdengine.domain.SuperTableDescribeVO;
import com.basiclab.iot.tdengine.domain.model.SuperTableDTO;
import com.basiclab.iot.tdengine.domain.model.TableDTO;
import com.basiclab.iot.tdengine.domain.model.TagsSelectDTO;
import com.basiclab.iot.tdengine.domain.query.TDDeviceDataHistoryRequest;
import com.basiclab.iot.tdengine.domain.query.TDDeviceDataRequest;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;

/**
 * TdEngineService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface TdEngineService {
    /**
     * 创建数据库
     *
     * @param dataBaseName
     */
    default void createDatabase(@Param("dataBaseName") String dataBaseName) {

    }

    /**
     * 创建超级表
     *
     * @param dataBaseName
     * @param superTableName
     */
    default void createSuperTable(@Param("dataBaseName") String dataBaseName, @Param("superTableName") String superTableName) {

    }

    /**
     * 创建超级表及字段
     *
     * @param superTableDTO
     */
    default void createSuperTableAndColumn(SuperTableDTO superTableDTO) {

    }

    /**
     * 创建子表
     *
     * @param tableDTO
     */
    default void createSubTable(TableDTO tableDTO) {

    }

    /**
     * 删除超级表
     *
     * @param dataBaseName
     * @param superTableName
     */
    default void dropSuperTable(@Param("dataBaseName") String dataBaseName, @Param("superTableName") String superTableName) {

    }

    /**
     * 新增字段
     *
     * @param superTableName
     * @param fields
     */
    default void alterSuperTableColumn(@Param("dataBaseName") String dataBaseName, @Param("superTableName") String superTableName,
                                       @Param("fields") Fields fields) {

    }

    /**
     * 删除字段
     *
     * @param dataBaseName
     * @param superTableName
     * @param fields
     */
    default void dropSuperTableColumn(@Param("dataBaseName") String dataBaseName, @Param("superTableName") String superTableName,
                                      @Param("fields") Fields fields) {

    }

    /**
     * 查询表结构
     *
     * @param dataBaseName
     * @param tableName
     */
    default List<SuperTableDescribeVO> describeSuperOrSubTable(@Param("dataBaseName") String dataBaseName, @Param("tableName") String tableName) {

        return null;
    }

    /**
     * 添加标签
     *
     * @param dataBaseName
     * @param superTableName
     * @param fields
     */
    default void alterSuperTableTag(@Param("dataBaseName") String dataBaseName, @Param("superTableName") String superTableName,
                                    @Param("fields") Fields fields) {

    }

    /**
     * 删除标签
     *
     * @param dataBaseName
     * @param superTableName
     * @param fields
     */
    default void dropSuperTableTag(@Param("dataBaseName") String dataBaseName, @Param("superTableName") String superTableName, @Param("fields") Fields fields) {

    }

    /**
     * 修改标签名
     *
     * @param dataBaseName
     * @param superTableName
     * @param oldName
     * @param newName
     */
    default void alterSuperTableTagRename(@Param("dataBaseName") String dataBaseName, @Param("superTableName") String superTableName,
                                          @Param("oldName") String oldName, @Param("newName") String newName) {

    }

    /**
     * 新增数据
     *
     * @param tableDTO
     */
    default void insertTableData(TableDTO tableDTO) {

    }

    /**
     * 查询最新数据
     *
     * @param tagsSelectDTO
     * @return
     */
    default Map<String, Map<String, Object>> getLastDataByTags(TagsSelectDTO tagsSelectDTO) {
        return null;
    }

    /**
     * Retrieves the latest data from the specified table within the given database.
     * If both startTime and endTime are provided, it fetches records within that time range.
     * Otherwise, it retrieves the last recorded data.
     *
     * @param dataBaseName The name of the database.
     * @param tableName    The name of the table.
     * @param startTime    The start time for the query range (can be null).
     * @param endTime      The end time for the query range (can be null).
     * @return A {@link List<Map<String,Object>>} containing the latest data.
     */
    default List<Map<String, Object>> getDataInRangeOrLastRecord(String dataBaseName, String tableName, Long startTime, Long endTime) {
        return null;
    }


    default List<Map<String, Object>> selectByTimesTamp(SelectDto selectDto) throws Exception {
        return null;
    }

    default List<Map<String, Object>> getLastData(SelectDto selectDto) throws Exception {
        return null;
    }

    /**
     * 通过设备标识查询设备最新数据
     *
     * @param tdDeviceDataRequest 请求体
     * @return DeviceData
     */
    List<DeviceData> getLastRowsListByIdentifier(TDDeviceDataRequest tdDeviceDataRequest);

    /**
     * 查询运行时属性历史数据
     *
     * @param request
     * @return
     */
    List<TDDeviceDataResp> deviceInfoHistoryPage(TDDeviceDataHistoryRequest request);

    /**
     * 查询设备时序数据（通用查询方法）
     * 支持查询属性上报、事件上报、服务调用响应等不同类型的时序数据
     *
     * @param request 查询请求
     * @return 时序数据列表
     */
    List<Map<String, Object>> queryDeviceTimeSeriesData(com.basiclab.iot.tdengine.domain.query.DeviceTimeSeriesQueryRequest request);
}
