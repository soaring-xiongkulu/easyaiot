package com.basiclab.iot.common.mqs;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface ProductTopicConstant {

    interface IotGateway {


        /**
         * 更新设备通道消息
         */
        String SYNC_MSG_TOPIC = "sync-msg";
        /**
         * 更新通道消息状态消息
         */
        String SYNC_STATUS_MSG_TOPIC = "sync-status-msg";
        /**
         * 前端控制指令消息
         */
        String FRONT_END_CMD_MSG_TOPIC = "front-end-cmd";
        /**
         * 设备录像信息查询消息
         */
        String GB_RECORD_QUERY_MSG_TOPIC = "gb-record-query-msg";
        /**
         * 设备回放消息
         */
        String PLAY_BACK_MSG_TOPIC = "play-back-msg";
        /**
         * 设备抓拍
         */
        String VIDEO_SNAPSHOT_MSG_TOPIC = "video-snapshot-msg";
    }
}
