package com.basiclab.iot.dataset.domain.dataset.vo;

import com.basiclab.iot.common.domain.PageParam;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.ToString;
import org.springframework.format.annotation.DateTimeFormat;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

/**
 * DatasetTaskResultPageReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 标注任务结果分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class DatasetTaskResultPageReqVO extends PageParam {

    @Schema(description = "数据集图片ID", example = "10634")
    private Long datasetImageId;

    @Schema(description = "模型ID", example = "28292")
    private Long modelId;

    @Schema(description = "是否有标注[0:无,1:有]")
    private Integer hasAnno;

    @Schema(description = "标注信息")
    private String annos;

    @Schema(description = "任务类型[0:智能标注,1:人员标注,2:审核]", example = "2")
    private Integer taskType;

    @Schema(description = "标注或审核的用户id", example = "15486")
    private Long userId;

    @Schema(description = "通过状态[0:待审核,1:通过,2:驳回]", example = "1")
    private Integer passStatus;

    @Schema(description = "任务ID", example = "6721")
    private Long taskId;

    @Schema(description = "驳回原因", example = "不好")
    private String reason;

    @Schema(description = "是否修改过[0:否,1是]")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private Integer[] isUpdate;

}