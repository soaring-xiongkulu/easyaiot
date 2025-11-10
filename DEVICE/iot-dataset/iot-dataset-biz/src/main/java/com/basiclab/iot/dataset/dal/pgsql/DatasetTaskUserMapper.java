package com.basiclab.iot.dataset.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTaskUserDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskUserPageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 标注任务用户 Mapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DatasetTaskUserMapper extends BaseMapperX<DatasetTaskUserDO> {

    default PageResult<DatasetTaskUserDO> selectPage(DatasetTaskUserPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<DatasetTaskUserDO>()
                .eqIfPresent(DatasetTaskUserDO::getTaskId, reqVO.getTaskId())
                .eqIfPresent(DatasetTaskUserDO::getUserId, reqVO.getUserId())
                .eqIfPresent(DatasetTaskUserDO::getAuditUserId, reqVO.getAuditUserId())
                .orderByDesc(DatasetTaskUserDO::getUpdateTime));
    }

}