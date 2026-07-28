package com.basiclab.iot.transform.runtime.dal.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.transform.runtime.dal.dataobject.PushRecordDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface PushRecordMapper extends BaseMapper<PushRecordDO> {

    @Select("SELECT * FROM transform_push_record WHERE deleted = 0 AND ("
            + " push_status IN ('PENDING','FAILED')"
            + " OR (push_status = 'RELAYING' AND update_time < NOW() - INTERVAL '5 minutes')"
            + ") AND (next_retry_time IS NULL OR next_retry_time <= NOW()) "
            + "ORDER BY create_time ASC LIMIT #{limit} FOR UPDATE SKIP LOCKED")
    List<PushRecordDO> claimBatch(@Param("limit") int limit);
}
