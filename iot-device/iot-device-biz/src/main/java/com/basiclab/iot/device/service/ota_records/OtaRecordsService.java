package com.basiclab.iot.device.service.ota_records;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.ota_records.vo.*;
import com.basiclab.iot.device.dal.dataobject.ota_records.OtaRecordsDO;
import com.basiclab.iot.common.domain.PageResult;

/**
 * OTA升级记录 Service 接口
 *
 * @author BasicLab
 */
public interface OtaRecordsService {

    /**
     * 创建OTA升级记录
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createRecords(@Valid OtaRecordsSaveReqVO createReqVO);

    /**
     * 更新OTA升级记录
     *
     * @param updateReqVO 更新信息
     */
    void updateRecords(@Valid OtaRecordsSaveReqVO updateReqVO);

    /**
     * 删除OTA升级记录
     *
     * @param id 编号
     */
    void deleteRecords(Long id);

    /**
     * 获得OTA升级记录
     *
     * @param id 编号
     * @return OTA升级记录
     */
    OtaRecordsDO getRecords(Long id);

    /**
     * 获得OTA升级记录分页
     *
     * @param pageReqVO 分页查询
     * @return OTA升级记录分页
     */
    PageResult<OtaRecordsDO> getRecordsPage(OtaRecordsPageReqVO pageReqVO);

}