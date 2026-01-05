package com.genersoft.iot.vmp.media.abl.bean.hook;

public class OnRecordProgressABLHookParam extends OnRecordMp4ABLHookParam{
    private Integer currentFileDuration;
    private Integer TotalVideoDuration;
    // startTime 和 endTime 继承自父类，不需要重新定义

    public Integer getCurrentFileDuration() {
        return currentFileDuration;
    }

    public void setCurrentFileDuration(Integer currentFileDuration) {
        this.currentFileDuration = currentFileDuration;
    }

    public Integer getTotalVideoDuration() {
        return TotalVideoDuration;
    }

    public void setTotalVideoDuration(Integer totalVideoDuration) {
        TotalVideoDuration = totalVideoDuration;
    }

    // startTime 和 endTime 继承自父类 OnRecordMp4ABLHookParam
    // 如果需要覆盖，可以使用 @Override 注解，但需要返回正确的类型
}
