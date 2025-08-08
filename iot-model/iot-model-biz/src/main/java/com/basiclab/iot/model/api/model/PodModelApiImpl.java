package com.basiclab.iot.model.api.model;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.model.RemoteModelApi;
import com.basiclab.iot.model.dal.dataobject.ModelDO;
import com.basiclab.iot.model.dal.pgsql.ModelMapper;
import com.basiclab.iot.model.domain.model.vo.PodModelSaveReqVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class PodModelApiImpl implements RemoteModelApi {

    @Autowired
    private ModelMapper modelMapper;

    @Override
    public CommonResult<Integer> savePtModel(PodModelSaveReqVO saveReqVO) {
        ModelDO modelDO = new ModelDO();
        modelDO.setName(saveReqVO.getModelName());
        modelDO.setDescription(saveReqVO.getDescription());
        modelDO.setVersion(saveReqVO.getVersion());
        modelDO.setPtModelUrl(saveReqVO.getPtModelUrl());
        modelDO.setPtResultUrl(saveReqVO.getPtResultUrl());
        modelDO.setPublishStatus((short) 0); // 默认未发布
        Integer id = modelMapper.insert(modelDO);
        return CommonResult.success(id);
    }
}