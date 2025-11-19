package com.basiclab.iot.message.domain.entity;

import lombok.Data;

import java.util.Date;
import java.util.List;

/**
 * 用户组实体
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-19
 */
@Data
public class TPreviewUserGroup {
    private String id;

    private Integer msgType;

    private String userGroupName;

    private String previewUserId; //目标用户id,多个用,隔开。

    private Date createTime;

    private List<TPreviewUser> tPreviewUsers; //用户组中的目标用户集合
}
