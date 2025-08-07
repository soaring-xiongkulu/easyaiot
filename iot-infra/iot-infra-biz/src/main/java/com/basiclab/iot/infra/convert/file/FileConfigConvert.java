package com.basiclab.iot.infra.convert.file;

import com.basiclab.iot.infra.controller.admin.file.vo.config.FileConfigSaveReqVO;
import com.basiclab.iot.infra.dal.dataobject.file.FileConfigDO;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.factory.Mappers;

/**
 * 文件配置 Convert
 *
 * @author 深圳市深度智核科技有限责任公司
 */
@Mapper
public interface FileConfigConvert {

    FileConfigConvert INSTANCE = Mappers.getMapper(FileConfigConvert.class);

    @Mapping(target = "config", ignore = true)
    FileConfigDO convert(FileConfigSaveReqVO bean);

}
