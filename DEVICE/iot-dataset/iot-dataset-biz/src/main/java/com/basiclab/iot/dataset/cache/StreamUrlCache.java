package com.basiclab.iot.dataset.cache;



import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.basiclab.iot.dataset.dal.dataobject.DatasetFrameTaskDO;
import com.basiclab.iot.dataset.dal.pgsql.DatasetFrameTaskMapper;
import com.basiclab.iot.dataset.enums.dataset.DatasetFrameType;
import com.google.common.collect.Maps;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent

/**
 * StreamUrlCache
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicLong;

@Service
public class StreamUrlCache {
    private final List<Map<String, String>> cachedUrls = new CopyOnWriteArrayList<>();
    private final AtomicLong lastRefreshTime = new AtomicLong(0);

    @Value("${pipeline.frame.url-refresh-rate:1800000}")
    private long refreshInterval;

    private DatasetFrameTaskMapper repository;

    public StreamUrlCache(DatasetFrameTaskMapper repository) {
        this.repository = repository;
        refresh();
    }

    // 刷新缓存（带锁防止并发刷新）
    public synchronized void refresh() {
        cachedUrls.clear();
        lastRefreshTime.set(System.currentTimeMillis());
        LambdaQueryWrapper<DatasetFrameTaskDO> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.in(DatasetFrameTaskDO::getTaskType, DatasetFrameType.LIVE_VIDEO_FRAME.getKey());
        List<DatasetFrameTaskDO> datasetFrameTaskDOList = repository.selectList(queryWrapper);
        if (datasetFrameTaskDOList == null || datasetFrameTaskDOList.isEmpty()) {
            return;
        }
        datasetFrameTaskDOList.forEach(stream -> {
            Map<String, String> streamMap = Maps.newHashMap();
            streamMap.put("datasetId", String.valueOf(stream.getDatasetId()));
            streamMap.put("rtmpUrl", stream.getRtmpUrl());
            cachedUrls.add(streamMap);
        });
    }

    // 获取缓存URL列表
    public List<Map<String, String>> getCachedUrls() {
        // 自动刷新检查
        if (System.currentTimeMillis() - lastRefreshTime.get() > refreshInterval) {
            refresh();
        }
        return new ArrayList<>(cachedUrls);
    }

    // 手动刷新接口
    public void manualRefresh() {
        refresh();
    }
}