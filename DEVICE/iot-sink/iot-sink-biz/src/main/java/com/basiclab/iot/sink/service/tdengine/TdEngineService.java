package com.basiclab.iot.sink.service.tdengine;

import com.basiclab.iot.tdengine.domain.model.TableDTO;

/**
 * TDEngine 服务接口
 * <p>
 * 提供 TDEngine 数据库操作服务
 *
 * @author 翱翔的雄库鲁
 */
public interface TdEngineService {

    /**
     * 插入表数据
     *
     * @param tableDTO 表数据DTO
     */
    void insertTableData(TableDTO tableDTO);
}

