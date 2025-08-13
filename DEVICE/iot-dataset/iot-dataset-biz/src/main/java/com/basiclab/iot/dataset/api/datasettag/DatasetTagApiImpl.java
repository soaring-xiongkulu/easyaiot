package com.basiclab.iot.dataset.api.datasettag;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.api.RemoteDatasetTagApi;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTagDO;
import com.basiclab.iot.dataset.dal.dataobject.WarehouseDatasetDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagRespVO;
import com.basiclab.iot.dataset.domain.warehouse.vo.WarehouseDatasetPageReqVO;
import com.basiclab.iot.dataset.service.DatasetTagService;
import com.basiclab.iot.dataset.service.WarehouseDatasetService;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

import static com.basiclab.iot.common.domain.CommonResult.success;

@RestController
@Validated
@Tag(name = "RPC服务 - 数据集和数据仓标签实现")
public class DatasetTagApiImpl implements RemoteDatasetTagApi {

    @Resource
    private DatasetTagService datasetTagService;

    @Resource
    private WarehouseDatasetService warehouseDatasetService;

    @Override
    public CommonResult<List<DatasetTagRespVO>> listTagsByDataset(Long datasetId) {
        // 构建分页查询请求（不分页）
        DatasetTagPageReqVO pageReqVO = new DatasetTagPageReqVO();
        pageReqVO.setDatasetId(datasetId);
        pageReqVO.setPageNo(1);
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE); // 获取全部数据

        // 执行查询并转换结果
        PageResult<DatasetTagDO> pageResult = datasetTagService.getDatasetTagPage(pageReqVO);
        List<DatasetTagRespVO> result = BeanUtils.toBean(pageResult.getList(), DatasetTagRespVO.class);

        return success(result);
    }

    @Override
    public CommonResult<List<DatasetTagRespVO>> listTagsByWarehouse(Long warehouseId) {
        // 获取数据仓关联的所有数据集
        WarehouseDatasetPageReqVO pageReqVO = new WarehouseDatasetPageReqVO();
        pageReqVO.setWarehouseId(warehouseId);
        pageReqVO.setPageNo(1);
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE); // 获取全部数据

        PageResult<WarehouseDatasetDO> warehouseDatasets = warehouseDatasetService.getWarehouseDatasetPage(pageReqVO);

        // 提取所有数据集ID
        List<Long> datasetIds = warehouseDatasets.getList().stream()
                .map(WarehouseDatasetDO::getDatasetId)
                .collect(Collectors.toList());

        // 获取所有数据集的标签
        List<DatasetTagRespVO> allTags = new ArrayList<>();
        for (Long datasetId : datasetIds) {
            CommonResult<List<DatasetTagRespVO>> tagsResult = this.listTagsByDataset(datasetId);
            if (tagsResult != null && tagsResult.getData() != null) {
                allTags.addAll(tagsResult.getData());
            }
        }

        return success(allTags);
    }
}