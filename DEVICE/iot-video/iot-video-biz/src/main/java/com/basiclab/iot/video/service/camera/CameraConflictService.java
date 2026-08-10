package com.basiclab.iot.video.service.camera;

import com.basiclab.iot.video.dal.AlgorithmTaskRepository;
import com.basiclab.iot.video.dal.StreamForwardTaskRepository;
import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.domain.StreamForwardTaskRow;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Service
@RequiredArgsConstructor
public class CameraConflictService {

    private final AlgorithmTaskRepository algorithmTaskRepository;
    private final StreamForwardTaskRepository streamForwardTaskRepository;

    public List<String> listConflicts(String taskType) {
        Set<String> conflictIds = new HashSet<>();
        if (taskType == null || taskType.isBlank() || "stream_forward".equals(taskType)) {
            for (AlgorithmTaskRow task : algorithmTaskRepository.findEnabledLocal()) {
                if ("running".equalsIgnoreCase(task.getRunStatus())) {
                    conflictIds.addAll(task.getDeviceIds());
                }
            }
        }
        if (taskType == null || taskType.isBlank() || "algorithm".equals(taskType)) {
            for (StreamForwardTaskRow task : streamForwardTaskRepository.findEnabledLocal()) {
                conflictIds.addAll(task.getDeviceIds());
            }
        }
        return conflictIds.stream().sorted().toList();
    }
}
