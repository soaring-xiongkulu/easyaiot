package com.basiclab.iot.message.domain.model.vo;

import com.alibaba.excel.annotation.ExcelProperty;
import com.alibaba.excel.annotation.write.style.ColumnWidth;
import lombok.Data;

@Data
public class TPreviewUserExcelVo {
    @ExcelProperty("消息通知类型")
    @ColumnWidth(20)
    private String msgType;

    @ExcelProperty("目标用户")
    @ColumnWidth(20)
    private String previewUser;
}
