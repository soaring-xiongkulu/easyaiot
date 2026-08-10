package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.RecordSpaceRepository;
import com.basiclab.iot.video.support.SpaceNodeSupport;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class RecordSpaceService {

    private final RecordSpaceRepository recordSpaceRepository;

    public Map<String, Object> listSpaces(int pageNo, int pageSize) {
        List<Map<String, Object>> all = recordSpaceRepository.listRootNodes(1, Integer.MAX_VALUE);
        List<Map<String, Object>> items = SpaceNodeSupport.paginate(all, pageNo, pageSize);
        Map<String, Object> result = new java.util.LinkedHashMap<>();
        result.put("items", items);
        result.put("total", all.size());
        result.put("parent_key", "root");
        result.put("breadcrumbs", SpaceNodeSupport.rootBreadcrumbs());
        result.put("is_search", false);
        result.put("scope", null);
        return result;
    }
}
