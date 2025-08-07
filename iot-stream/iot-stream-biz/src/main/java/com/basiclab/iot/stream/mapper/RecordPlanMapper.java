package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.stream.service.bean.RecordPlan;
import com.basiclab.iot.stream.service.bean.RecordPlanItem;
import org.apache.ibatis.annotations.Param;

import java.util.List;

public interface RecordPlanMapper {

    /**
     * 添加录制计划
     *
     * @param plan 录制计划实体
     */
    void add(RecordPlan plan);

    /**
     * 批量添加录制计划项
     *
     * @param planId     录制计划ID
     * @param planItemList 录制计划项列表
     */
    void batchAddItem(@Param("planId") int planId, List<RecordPlanItem> planItemList);

    /**
     * 根据ID查询录制计划
     *
     * @param planId 录制计划ID
     * @return 录制计划实体
     */
    RecordPlan get(@Param("planId") Integer planId);

    /**
     * 查询录制计划列表
     *
     * @param query 查询条件
     * @return 录制计划列表
     */
    List<RecordPlan> query(@Param("query") String query);

    /**
     * 更新录制计划
     *
     * @param plan 录制计划实体
     */
    void update(RecordPlan plan);

    /**
     * 删除录制计划
     *
     * @param planId 录制计划ID
     */
    void delete(@Param("planId") Integer planId);

    /**
     * 根据录制计划ID查询录制计划项列表
     *
     * @param planId 录制计划ID
     * @return 录制计划项列表
     */
    List<RecordPlanItem> getItemList(@Param("planId") Integer planId);

    /**
     * 清空指定录制计划ID下的录制计划项
     *
     * @param planId 录制计划ID
     */
    void cleanItems(@Param("planId") Integer planId);

    /**
     * 查询正在录制的设备频道ID列表
     *
     * @param week 周几
     * @param index 时间索引
     * @return 设备频道ID列表
     */
    List<Integer> queryRecordIng(@Param("week") int week, @Param("index") int index);
}