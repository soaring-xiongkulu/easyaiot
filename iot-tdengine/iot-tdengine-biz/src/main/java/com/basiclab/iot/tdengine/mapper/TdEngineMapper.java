package com.basiclab.iot.tdengine.mapper;

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
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;

/**
 * @ClassDescription:
 * @ClassName: TdEngineMapper
 * @Author: iot
 * @Date: 2021-12-27 14:52:34
 * @Version 1.0
 */
@Mapper
public interface TdEngineMapper {


    /**
     * 创建数据库
     *
     * @param dataBaseName
     */
    void createDatabase(@Param("dataBaseName") String dataBaseName);

    /**
     * 创建超级表
     *
     * @param dataBaseName
     * @param superTableName
     */
    void createSuperTable(@Param("dataBaseName") String dataBaseName, @Param("superTableName") String superTableName);

    /**
     * 创建超级表及字段
     *
     * @param superTableDTO
     */
    void createSuperTableAndColumn(SuperTableDTO superTableDTO);


    /**
     * 创建子表
     *
     * @param tableDTO
     */
    void createSubTable(TableDTO tableDTO);

    /**
     * 删除超级表
     *
     * @param dataBaseName
     * @param superTableName
     */
    void dropSuperTable(@Param("dataBaseName") String dataBaseName, @Param("superTableName") String superTableName);

    /**
     * 新增字段
     *
     * @param dataBaseName
     * @param superTableName
     * @param fields
     */
    void alterSuperTableColumn(@Param("dataBaseName") String dataBaseName, @Param("superTableName") String superTableName, @Param("fields") Fields fields);

    /**
     * 删除字段
     *
     * @param dataBaseName
     * @param superTableName
     * @param fields
     */
    void dropSuperTableColumn(@Param("dataBaseName") String dataBaseName, @Param("superTableName") String superTableName, @Param("fields") Fields fields);

    /**
     * 查询表结构
     *
     * @param dataBaseName
     * @param tableName
     */
    List<SuperTableDescribeVO> describeSuperOrSubTable(@Param("dataBaseName") String dataBaseName, @Param("tableName") String tableName);

    /**
     * 添加标签
     *
     * @param dataBaseName
     * @param superTableName
     * @param fields
     */
    void alterSuperTableTag(@Param("dataBaseName") String dataBaseName, @Param("superTableName") String superTableName, @Param("fields") Fields fields);

    /**
     * 删除标签
     *
     * @param dataBaseName
     * @param superTableName
     * @param fields
     */
    void dropSuperTableTag(@Param("dataBaseName") String dataBaseName, @Param("superTableName") String superTableName, @Param("fields") Fields fields);

    /**
     * 修改标签名
     *
     * @param dataBaseName
     * @param superTableName
     * @param oldName
     * @param newName
     */
    void alterSuperTableTagRename(@Param("dataBaseName") String dataBaseName, @Param("superTableName") String superTableName, @Param("oldName") String oldName,
                                  @Param("newName") String newName);

    /**
     * 新增数据
     *
     * @param tableDTO
     */
    void insertTableData(TableDTO tableDTO);

    /**
     * 查询最新数据
     *
     * @param tagsSelectDTO
     * @return
     */
    List<Map<String, Object>> getLastDataByTags(TagsSelectDTO tagsSelectDTO);

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
    List<Map<String, Object>> getDataInRangeOrLastRecord(
            @Param("dataBaseName") String dataBaseName,
            @Param("tableName") String tableName,
            @Param("startTime") Long startTime,
            @Param("endTime") Long endTime);

    List<Map<String, Object>> selectByTimestamp(SelectDto selectDto);


    List<Map<String, Object>> getLastData(SelectDto selectDto);

    /**
     * 通过设备标识查询设备最新数据
     *
     * @param tdDeviceDataRequest 请求体
     * @return DeviceData
     */
    List<DeviceData> getLastRowsListByIdentifier(TDDeviceDataRequest tdDeviceDataRequest);

    /**
     * 查询运行时属性历史数据
     * @param request
     * @return
     */
    List<TDDeviceDataResp> getDeviceHistory(TDDeviceDataHistoryRequest request);
}
