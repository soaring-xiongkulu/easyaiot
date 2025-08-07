package com.basiclab.iot.stream.service;


import com.basiclab.iot.stream.bean.MobilePosition;
import com.basiclab.iot.stream.bean.Platform;
import com.basiclab.iot.stream.service.bean.GPSMsgInfo;

import java.util.List;

public interface IMobilePositionService {

    void add(List<MobilePosition> mobilePositionList);

    void add(MobilePosition mobilePosition);

    List<MobilePosition> queryMobilePositions(String deviceId, String channelId, String startTime, String endTime);

    List<Platform> queryEnablePlatformListWithAsMessageChannel();

    MobilePosition queryLatestPosition(String deviceId);

    void updateStreamGPS(List<GPSMsgInfo> gpsMsgInfoList);

}
