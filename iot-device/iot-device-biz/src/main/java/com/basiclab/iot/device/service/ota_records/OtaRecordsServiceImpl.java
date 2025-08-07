package com.basiclab.iot.device.service.ota_records;

import com.basiclab.iot.device.dal.mysql.ota_records.OtaRecordsMapper;
import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.ota_records.vo.*;
import com.basiclab.iot.device.dal.dataobject.ota_records.OtaRecordsDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;


import static com.basiclab.iot.device.enums.ErrorCodeConstants.OTA_RECORDS_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * OTA升级记录 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class OtaRecordsServiceImpl implements OtaRecordsService {

    @Resource
    private OtaRecordsMapper otaRecordsMapper;

    @Override
    public Long createRecords(OtaRecordsSaveReqVO createReqVO) {
        // 插入
        OtaRecordsDO records = BeanUtils.toBean(createReqVO, OtaRecordsDO.class);
        otaRecordsMapper.insert(records);
        // 返回
        return records.getId();
    }

    @Override
    public void updateRecords(OtaRecordsSaveReqVO updateReqVO) {
        // 校验存在
        validateRecordsExists(updateReqVO.getId());
        // 更新
        OtaRecordsDO updateObj = BeanUtils.toBean(updateReqVO, OtaRecordsDO.class);
        otaRecordsMapper.updateById(updateObj);
    }

    @Override
    public void deleteRecords(Long id) {
        // 校验存在
        validateRecordsExists(id);
        // 删除
        otaRecordsMapper.deleteById(id);
    }

    private void validateRecordsExists(Long id) {
        if (otaRecordsMapper.selectById(id) == null) {
            throw exception(OTA_RECORDS_NOT_EXISTS);
        }
    }

    @Override
    public OtaRecordsDO getRecords(Long id) {
        return otaRecordsMapper.selectById(id);
    }

    @Override
    public PageResult<OtaRecordsDO> getRecordsPage(OtaRecordsPageReqVO pageReqVO) {
        return otaRecordsMapper.selectPage(pageReqVO);
    }

}