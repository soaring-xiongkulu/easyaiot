package com.basiclab.iot.sink.dal.mapper;

import com.baomidou.dynamic.datasource.annotation.DS;
import com.basiclab.iot.tdengine.domain.model.TableDTO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * TDEngine Mapper 接口
 * <p>
 * 用于直接操作 TDEngine 数据库
 *
 * @author 翱翔的雄库鲁
 */
@Mapper
@DS("tdengine")
public interface TdEngineMapper {

    /**
     * 插入表数据
     *
     * @param tableDTO 表数据DTO
     */
    void insertTableData(TableDTO tableDTO);
}

