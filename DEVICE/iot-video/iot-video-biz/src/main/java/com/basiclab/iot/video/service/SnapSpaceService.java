package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.SnapSpaceRepository;
import com.basiclab.iot.video.support.SpaceNodeSupport;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class SnapSpaceService {

    private final SnapSpaceRepository snapSpaceRepository;

    public Map<String, Object> listSpaces(int pageNo, int pageSize) {
        List<Map<String, Object>> items = snapSpaceRepository.listRootNodes(pageNo, pageSize);
        Map<String, Object> result = new java.util.LinkedHashMap<>();
        result.put("items", items);
        result.put("total", snapSpaceRepository.count());
        result.put("parent_key", "root");
        result.put("breadcrumbs", SpaceNodeSupport.rootBreadcrumbs());
        result.put("is_search", false);
        result.put("scope", null);
        return result;
    }
}
