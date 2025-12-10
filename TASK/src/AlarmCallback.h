/*
 * HTTP Alarm Callback Wrapper
 * Sends detection results to AI module via HTTP POST
 */

#ifndef ALARM_CALLBACK_H
#define ALARM_CALLBACK_H

#include <string>
#include <vector>
#include <json/json.h>
#include <httplib.h>
#include <glog/logging.h>
#include "Datatype.h"

class AlarmCallback {
public:
    /**
     * 构造函数
     * @param hookUrl 回调URL（例如: http://localhost:5000/api/alarm/callback/123）
     */
    AlarmCallback(const std::string& hookUrl);
    
    ~AlarmCallback();
    
    /**
     * 发送告警回调
     * @param taskId 任务ID
     * @param detections 检测结果列表
     * @param regionId 触发的报警区域ID
     * @param timestamp 时间戳
     * @return 发送成功返回true，失败返回false
     */
    bool sendAlarm(
        int taskId,
        const std::vector<DetectObject>& detections,
        const std::string& regionId,
        const std::string& timestamp
    );
    
    /**
     * 测试连接
     * @return 连接成功返回true
     */
    bool testConnection();

private:
    /**
     * 构建JSON请求体
     */
    std::string buildJsonBody(
        int taskId,
        const std::vector<DetectObject>& detections,
        const std::string& regionId,
        const std::string& timestamp
    );
    
    /**
     * 解析URL
     */
    bool parseUrl(const std::string& url, std::string& host, int& port, std::string& path);

private:
    std::string hookUrl_;
    std::string host_;
    int port_;
    std::string path_;
    httplib::Client* client_;
};

#endif // ALARM_CALLBACK_H
