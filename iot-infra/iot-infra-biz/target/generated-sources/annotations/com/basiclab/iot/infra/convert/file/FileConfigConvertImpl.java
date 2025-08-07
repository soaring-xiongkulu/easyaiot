package com.basiclab.iot.infra.convert.file;

import com.basiclab.iot.infra.controller.admin.file.vo.config.FileConfigSaveReqVO;
import com.basiclab.iot.infra.dal.dataobject.file.FileConfigDO;
import javax.annotation.Generated;

@Generated(
    value = "org.mapstruct.ap.MappingProcessor",
    date = "2025-06-14T19:15:29+0800",
    comments = "version: 1.5.5.Final, compiler: javac, environment: Java 1.8.0_333 (Oracle Corporation)"
)
public class FileConfigConvertImpl implements FileConfigConvert {

    @Override
    public FileConfigDO convert(FileConfigSaveReqVO bean) {
        if ( bean == null ) {
            return null;
        }

        FileConfigDO.FileConfigDOBuilder fileConfigDO = FileConfigDO.builder();

        fileConfigDO.id( bean.getId() );
        fileConfigDO.name( bean.getName() );
        fileConfigDO.storage( bean.getStorage() );
        fileConfigDO.remark( bean.getRemark() );

        return fileConfigDO.build();
    }
}
