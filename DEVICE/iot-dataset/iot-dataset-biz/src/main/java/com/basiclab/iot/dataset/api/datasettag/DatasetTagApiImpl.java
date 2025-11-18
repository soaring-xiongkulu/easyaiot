package com.basiclab.iot.dataset.api.datasettag;



import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.RemoteDatasetTagApi;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTagDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagRespVO;
import com.basiclab.iot.dataset.service.DatasetTagService;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import java.util.List;

import static com.basiclab.iot.common.domain.

/**
 * DatasetTagApiImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

CommonResult.success;

@RestController
@Validated
@Tag(name = "RPC服务 - 数据集和数据仓标签实现")
public class DatasetTagApiImpl implements RemoteDatasetTagApi {

    @Resource
    private DatasetTagService datasetTagService;

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
}