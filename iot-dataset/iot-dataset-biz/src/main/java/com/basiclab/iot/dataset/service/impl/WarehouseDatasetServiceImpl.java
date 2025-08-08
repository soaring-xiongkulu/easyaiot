package com.basiclab.iot.dataset.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.WarehouseDatasetDO;
import com.basiclab.iot.dataset.dal.pgsql.WarehouseDatasetMapper;
import com.basiclab.iot.dataset.domain.warehouse.vo.WarehouseDatasetPageReqVO;
import com.basiclab.iot.dataset.domain.warehouse.vo.WarehouseDatasetSaveReqVO;
import com.basiclab.iot.dataset.service.WarehouseDatasetService;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.dataset.enums.ErrorCodeConstants.WAREHOUSE_DATASET_NOT_EXISTS;


/**
 * 数据仓数据集关联 Service 实现类
 *
 * @author IoT
 */
@Service
@Validated
public class WarehouseDatasetServiceImpl implements WarehouseDatasetService {

    @Resource
    private WarehouseDatasetMapper warehouseDatasetMapper;

    @Override
    public Long createWarehouseDataset(WarehouseDatasetSaveReqVO createReqVO) {
        // 插入
        WarehouseDatasetDO dataset = BeanUtils.toBean(createReqVO, WarehouseDatasetDO.class);
        warehouseDatasetMapper.insert(dataset);
        // 返回
        return dataset.getId();
    }

    @Override
    public void updateWarehouseDataset(WarehouseDatasetSaveReqVO updateReqVO) {
        // 校验存在
        validateWarehouseDatasetExists(updateReqVO.getId());
        // 更新
        WarehouseDatasetDO updateObj = BeanUtils.toBean(updateReqVO, WarehouseDatasetDO.class);
        warehouseDatasetMapper.updateById(updateObj);
    }

    @Override
    public void deleteWarehouseDataset(Long id) {
        // 校验存在
        validateWarehouseDatasetExists(id);
        // 删除
        warehouseDatasetMapper.deleteById(id);
    }

    private void validateWarehouseDatasetExists(Long id) {
        if (warehouseDatasetMapper.selectById(id) == null) {
            throw exception(WAREHOUSE_DATASET_NOT_EXISTS);
        }
    }

    @Override
    public WarehouseDatasetDO getWarehouseDataset(Long id) {
        return warehouseDatasetMapper.selectById(id);
    }

    @Override
    public PageResult<WarehouseDatasetDO> getWarehouseDatasetPage(WarehouseDatasetPageReqVO pageReqVO) {
        return warehouseDatasetMapper.selectPage(pageReqVO);
    }

}