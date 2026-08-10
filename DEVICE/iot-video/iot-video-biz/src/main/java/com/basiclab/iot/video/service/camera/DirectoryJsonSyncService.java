package com.basiclab.iot.video.service.camera;

import com.basiclab.iot.video.dal.DeviceDirectoryRepository;
import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceDirectoryRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 设备目录 JSON 校验与同步（与 Python {@code directory_json_sync_service.py} / WEB directoryJson.ts 规则一致）。
 */
@Service
@RequiredArgsConstructor
public class DirectoryJsonSyncService {

    static final String DEFAULT_DIRECTORY_NAME = "默认分组";

    private final DeviceDirectoryRepository directoryRepository;
    private final DeviceRepository deviceRepository;

    @SuppressWarnings("unchecked")
    public List<Map<String, Object>> parsePayload(Object data) {
        if (data instanceof List<?> list) {
            return (List<Map<String, Object>>) list;
        }
        if (data instanceof Map<?, ?> map && map.get("tree") instanceof List<?> tree) {
            return (List<Map<String, Object>>) tree;
        }
        throw new VideoBusinessException(400, "请使用目录数组，或 { \"tree\": [...] }");
    }

    public void validateTree(List<Map<String, Object>> nodes) {
        if (nodes == null) {
            throw new VideoBusinessException(400, "根节点须为数组");
        }
        for (int i = 0; i < nodes.size(); i++) {
            validateNode(nodes.get(i), "[" + i + "]");
        }
        assertNoDuplicateDevices(nodes);
    }

    public void syncFromJson(List<Map<String, Object>> nodes) {
        validateTree(nodes);
        directoryRepository.ensureDefaultDirectory();
        normalizeJsonRootParentIds(nodes);

        List<ForestNode> roots = buildDirectoryForest(null);
        Map<String, Integer> pathCache = new HashMap<>();
        for (FlatEntry item : flattenWithPath(roots, "")) {
            pathCache.put(item.path(), item.id());
        }

        for (Map<String, Object> node : nodes) {
            syncNode(node, null, "", roots, pathCache);
        }

        List<ForestNode> rootsAfter = buildDirectoryForest(null);
        Set<String> keepPaths = collectJsonPaths(nodes, "");
        keepPaths.add(DEFAULT_DIRECTORY_NAME);
        pruneExtraDirectories(rootsAfter, keepPaths);
    }

    private void validateNode(Map<String, Object> node, String path) {
        if (node == null || node.isEmpty()) {
            throw new VideoBusinessException(400, path + " 须为对象");
        }
        String name = str(node.get("name"));
        if (name.isEmpty()) {
            throw new VideoBusinessException(400, path + ".name 不能为空");
        }
        if (DEFAULT_DIRECTORY_NAME.equals(name)) {
            throw new VideoBusinessException(400, "请勿在 JSON 中编辑「默认分组」，该分组由系统保留");
        }
        Object devices = node.get("devices");
        if (devices != null) {
            if (!(devices instanceof List<?> list)) {
                throw new VideoBusinessException(400, path + ".devices 须为设备 ID 字符串数组");
            }
            for (Object item : list) {
                if (!(item instanceof String) || str(item).isEmpty()) {
                    throw new VideoBusinessException(400, path + ".devices 须为设备 ID 字符串数组");
                }
            }
        }
        Object children = node.get("children");
        if (children != null) {
            if (!(children instanceof List<?> childList)) {
                throw new VideoBusinessException(400, path + ".children 须为数组");
            }
            for (int i = 0; i < childList.size(); i++) {
                Object child = childList.get(i);
                if (child instanceof Map<?, ?> childMap) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> childNode = (Map<String, Object>) childMap;
                    validateNode(childNode, path + ".children[" + i + "]");
                } else {
                    throw new VideoBusinessException(400, path + ".children[" + i + "] 须为对象");
                }
            }
        }
    }

    private void assertNoDuplicateDevices(List<Map<String, Object>> nodes) {
        Map<String, String> seen = new HashMap<>();
        walkDuplicateCheck(nodes, "", seen);
    }

    private void walkDuplicateCheck(List<Map<String, Object>> nodeList, String parentDir, Map<String, String> seen) {
        for (Map<String, Object> node : nodeList) {
            String name = str(node.get("name"));
            String dirLabel = parentDir.isEmpty() ? name : parentDir + " / " + name;
            Object devicesObj = node.get("devices");
            if (devicesObj instanceof List<?> devices) {
                for (Object rawId : devices) {
                    String deviceId = str(rawId);
                    if (deviceId.isEmpty()) {
                        continue;
                    }
                    String firstDir = seen.get(deviceId);
                    if (firstDir != null) {
                        throw new VideoBusinessException(400,
                                "摄像头「" + deviceId + "」在「" + firstDir + "」与「" + dirLabel + "」中重复，一个摄像头只能出现一次");
                    }
                    seen.put(deviceId, dirLabel);
                }
            }
            Object childrenObj = node.get("children");
            if (childrenObj instanceof List<?> children && !children.isEmpty()) {
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> childNodes = (List<Map<String, Object>>) childrenObj;
                walkDuplicateCheck(childNodes, dirLabel, seen);
            }
        }
    }

    private void normalizeJsonRootParentIds(List<Map<String, Object>> nodes) {
        for (Map<String, Object> node : nodes) {
            String key = str(node.get("name"));
            if (key.isEmpty() || DEFAULT_DIRECTORY_NAME.equals(key)) {
                continue;
            }
            for (DeviceDirectoryRow directory : directoryRepository.findAllByName(key)) {
                if (isDefaultDirectory(directory)) {
                    continue;
                }
                if (directory.getParentId() != null) {
                    directory.setParentId(null);
                    directoryRepository.update(directory);
                }
            }
        }
    }

    private void syncNode(
            Map<String, Object> node,
            Integer parentId,
            String parentPath,
            List<ForestNode> roots,
            Map<String, Integer> pathCache
    ) {
        int dirId = ensureDirectory(str(node.get("name")), parentId, roots, pathCache, parentPath);
        String path = dirPath(parentPath, str(node.get("name")));

        Object devicesObj = node.get("devices");
        if (devicesObj instanceof List<?> devices) {
            for (Object rawId : devices) {
                String deviceId = str(rawId);
                if (deviceId.isEmpty()) {
                    continue;
                }
                if (deviceRepository.findById(deviceId).isEmpty()) {
                    throw new VideoBusinessException(400, "设备不存在: " + deviceId);
                }
                deviceRepository.updateDirectoryId(deviceId, dirId);
            }
        }

        Object childrenObj = node.get("children");
        if (childrenObj instanceof List<?> children) {
            for (Object childObj : children) {
                if (childObj instanceof Map<?, ?> childMap) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> child = (Map<String, Object>) childMap;
                    syncNode(child, dirId, path, roots, pathCache);
                }
            }
        }
    }

    private int ensureDirectory(
            String name,
            Integer parentId,
            List<ForestNode> roots,
            Map<String, Integer> pathCache,
            String parentPath
    ) {
        String key = name.trim();
        String path = dirPath(parentPath, key);

        var rowOpt = directoryRepository.findByNameAndParentId(key, parentId);
        if (rowOpt.isPresent()) {
            DeviceDirectoryRow row = rowOpt.get();
            if (!(parentId == null && isDefaultDirectory(row))) {
                applyParentId(row, parentId);
                pathCache.put(path, row.getId());
                return row.getId();
            }
        }

        if (parentId == null) {
            directoryRepository.ensureDefaultDirectory();
            for (DeviceDirectoryRow candidate : directoryRepository.findAllByName(key)) {
                if (isDefaultDirectory(candidate)) {
                    continue;
                }
                applyParentId(candidate, null);
                pathCache.put(path, candidate.getId());
                ForestNode entry = new ForestNode(
                        candidate.getId(),
                        candidate.getName(),
                        null,
                        false,
                        buildDirectoryForest(candidate.getId())
                );
                injectIntoForest(roots, null, entry);
                return candidate.getId();
            }
        }

        ForestNode existing = findInForest(roots, parentId, key);
        if (existing != null) {
            DeviceDirectoryRow directory = directoryRepository.findById(existing.id())
                    .orElseThrow(() -> new VideoBusinessException(500, "目录不存在: ID=" + existing.id()));
            applyParentId(directory, parentId);
            pathCache.put(path, directory.getId());
            return directory.getId();
        }

        DeviceDirectoryRow directory = new DeviceDirectoryRow();
        directory.setName(key);
        directory.setParentId(parentId);
        directory.setDescription("");
        directory.setSortOrder(0);
        int id = directoryRepository.insert(directory);
        directory.setId(id);
        applyParentId(directory, parentId);
        pathCache.put(path, id);
        injectIntoForest(roots, parentId, new ForestNode(id, directory.getName(), directory.getParentId(), false, new ArrayList<>()));
        return id;
    }

    private void pruneExtraDirectories(List<ForestNode> roots, Set<String> keepPaths) {
        List<FlatEntry> flat = flattenWithPath(roots, "");
        List<FlatEntry> toRemove = flat.stream()
                .filter(d -> !d.isDefault() && !keepPaths.contains(d.path()))
                .sorted(Comparator.<FlatEntry>comparingInt(d -> d.path().split("/").length).reversed())
                .toList();

        for (FlatEntry item : toRemove) {
            DeviceDirectoryRow directory = directoryRepository.findById(item.id()).orElse(null);
            if (directory == null || isDefaultDirectory(directory)) {
                continue;
            }
            if (directoryRepository.countChildren(directory.getId()) > 0) {
                continue;
            }
            if (directoryRepository.countDevices(directory.getId()) > 0) {
                continue;
            }
            directoryRepository.delete(directory.getId());
        }
    }

    private List<ForestNode> buildDirectoryForest(Integer parentId) {
        List<DeviceDirectoryRow> directories = directoryRepository.findByParentId(parentId);
        List<ForestNode> result = new ArrayList<>();
        for (DeviceDirectoryRow directory : directories) {
            result.add(new ForestNode(
                    directory.getId(),
                    directory.getName(),
                    directory.getParentId(),
                    isDefaultDirectory(directory),
                    buildDirectoryForest(directory.getId())
            ));
        }
        return result;
    }

    private Set<String> collectJsonPaths(List<Map<String, Object>> nodes, String parentPath) {
        Set<String> paths = new HashSet<>();
        walkJsonPaths(nodes, parentPath, paths);
        return paths;
    }

    private void walkJsonPaths(List<Map<String, Object>> nodeList, String prefix, Set<String> paths) {
        for (Map<String, Object> node : nodeList) {
            String path = dirPath(prefix, str(node.get("name")));
            paths.add(path);
            Object childrenObj = node.get("children");
            if (childrenObj instanceof List<?> children && !children.isEmpty()) {
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> childNodes = (List<Map<String, Object>>) childrenObj;
                walkJsonPaths(childNodes, path, paths);
            }
        }
    }

    private void injectIntoForest(List<ForestNode> roots, Integer parentId, ForestNode entry) {
        if (parentId == null) {
            roots.add(entry);
            return;
        }
        if (walkInject(roots, parentId, entry)) {
            return;
        }
        roots.add(entry);
    }

    private boolean walkInject(List<ForestNode> nodes, Integer parentId, ForestNode entry) {
        for (ForestNode node : nodes) {
            if (parentId != null && node.id() == parentId) {
                node.children().add(entry);
                return true;
            }
            if (walkInject(node.children(), parentId, entry)) {
                return true;
            }
        }
        return false;
    }

    private ForestNode findInForest(List<ForestNode> roots, Integer parentId, String name) {
        String key = name.trim();
        if (parentId == null) {
            for (ForestNode node : roots) {
                if (key.equals(node.name())) {
                    return node;
                }
            }
            return null;
        }
        for (ForestNode node : roots) {
            if (parentId != null && node.id() == parentId) {
                for (ForestNode child : node.children()) {
                    if (key.equals(child.name())) {
                        return child;
                    }
                }
                return null;
            }
            ForestNode found = findInForest(node.children(), parentId, key);
            if (found != null) {
                return found;
            }
        }
        return null;
    }

    private List<FlatEntry> flattenWithPath(List<ForestNode> nodes, String parentPath) {
        List<FlatEntry> flat = new ArrayList<>();
        for (ForestNode node : nodes) {
            String path = dirPath(parentPath, node.name());
            flat.add(new FlatEntry(node.id(), path, node.isDefault()));
            flat.addAll(flattenWithPath(node.children(), path));
        }
        return flat;
    }

    private void applyParentId(DeviceDirectoryRow directory, Integer parentId) {
        if (isDefaultDirectory(directory)) {
            return;
        }
        if (!sameParent(directory.getParentId(), parentId)) {
            directory.setParentId(parentId);
            directoryRepository.update(directory);
        }
    }

    private boolean isDefaultDirectory(DeviceDirectoryRow directory) {
        return directory != null
                && DEFAULT_DIRECTORY_NAME.equals(directory.getName())
                && directory.getParentId() == null;
    }

    private static String dirPath(String parentPath, String name) {
        String n = name != null ? name.trim() : "";
        return parentPath == null || parentPath.isEmpty() ? n : parentPath + "/" + n;
    }

    private static boolean sameParent(Integer current, Integer requested) {
        if (current == null && requested == null) {
            return true;
        }
        return current != null && current.equals(requested);
    }

    private static String str(Object value) {
        return value != null ? String.valueOf(value).trim() : "";
    }

    private record ForestNode(int id, String name, Integer parentId, boolean isDefault, List<ForestNode> children) {
    }

    private record FlatEntry(int id, String path, boolean isDefault) {
    }
}
