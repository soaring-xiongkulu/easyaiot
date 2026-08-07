/*
 * HTTP Alarm Callback — VIDEO /video/alert/hook compatible payload
 */

#ifndef ALARM_CALLBACK_H
#define ALARM_CALLBACK_H

#include <string>
#include <vector>
#include <json/json.h>
#include <httplib.h>
#include <glog/logging.h>
#include "Datatype.h"

struct VideoAlertContext {
    std::string taskId;
    std::string deviceId;
    std::string deviceName;
    std::string taskType{"realtime"};
    std::string algorithmName{"detection"};
};

class AlarmCallback {
public:
    explicit AlarmCallback(const std::string& hookUrl);
    ~AlarmCallback();

    bool sendVideoAlert(
        const VideoAlertContext& ctx,
        const std::vector<DetectObject>& detections,
        const std::string& regionId,
        const std::string& timestamp,
        const std::string& imagePath = ""
    );

    /** Legacy DEVICE-style callback (kept for compatibility). */
    bool sendAlarm(
        int taskId,
        const std::vector<DetectObject>& detections,
        const std::string& regionId,
        const std::string& timestamp
    );

    bool testConnection();

private:
    std::string buildVideoJsonBody(
        const VideoAlertContext& ctx,
        const std::vector<DetectObject>& detections,
        const std::string& regionId,
        const std::string& timestamp,
        const std::string& imagePath
    );

    std::string buildLegacyJsonBody(
        int taskId,
        const std::vector<DetectObject>& detections,
        const std::string& regionId,
        const std::string& timestamp
    );

    bool parseUrl(const std::string& url, std::string& host, int& port, std::string& path);

private:
    std::string hookUrl_;
    std::string host_;
    int port_;
    std::string path_;
    httplib::Client* client_;
};

#endif // ALARM_CALLBACK_H
