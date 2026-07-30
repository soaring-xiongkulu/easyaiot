package com.basiclab.iot.transform.runtime.web;

import com.basiclab.iot.transform.core.control.TransformCommand;
import com.basiclab.iot.transform.core.control.TransformCommandAck;
import com.basiclab.iot.transform.core.domain.Contract;
import com.basiclab.iot.transform.core.domain.DlqRecord;
import com.basiclab.iot.transform.core.domain.MappingRule;
import com.basiclab.iot.transform.core.domain.OutboxRecord;
import com.basiclab.iot.transform.core.domain.Party;
import com.basiclab.iot.transform.core.domain.PipelineDef;
import com.basiclab.iot.transform.core.domain.RuntimeInstance;
import com.basiclab.iot.transform.runtime.service.ClusterControlService;
import com.basiclab.iot.transform.runtime.service.DeliveryPipelineService;
import com.basiclab.iot.transform.runtime.dal.TransformRepository;
import com.basiclab.iot.transform.runtime.service.MetricsService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Collection;
import java.util.List;
import java.util.Map;

/**
 * TRANSFORM 管理 API（网关 /admin-api/transform/** → StripPrefix=1 → /transform/**）。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@RestController
@RequestMapping("/transform")
@RequiredArgsConstructor
public class TransformAdminController {

    private final TransformRepository repository;
    private final DeliveryPipelineService pipeline;
    private final MetricsService metricsService;
    private final ClusterControlService clusterControlService;

    @GetMapping("/overview")
    public R<Map<String, Object>> overview() {
        List<RuntimeInstance> instances = clusterControlService.listInstances();
        long online = instances.stream().filter(RuntimeInstance::isOnline).count();
        return R.ok(Map.of(
                "parties", repository.partyCount(),
                "contracts", repository.contractCount(),
                "mappings", repository.mappingCount(),
                "pipelines", repository.pipelineCount(),
                "outbox", repository.outboxCount(),
                "dlq", repository.dlqCount(),
                "instances", instances.size(),
                "onlineInstances", online,
                "metrics", metricsService.snapshot()
        ));
    }

    @GetMapping("/cluster/workers")
    public R<Map<String, Object>> workers() {
        String localId = clusterControlService.localInstanceId();
        String localHost = clusterControlService.localHost();
        return R.ok(Map.of(
                "mode", "stateless",
                "groups", List.of(
                        "transform.kafka.consume.device",
                        "transform.http.deliver",
                        "transform.party.deliver"
                ),
                "commandTopic", "iot_transform_command",
                "commandAckTopic", "iot_transform_command_ack",
                "telemetryTopic", "iot_transform_telemetry",
                "localInstanceId", localId == null ? "" : localId,
                "localHost", localHost == null ? "" : localHost,
                "instances", clusterControlService.listInstances(),
                "metrics", metricsService.snapshot()
        ));
    }

    @GetMapping("/cluster/instances")
    public R<List<RuntimeInstance>> instances() {
        return R.ok(clusterControlService.listInstances());
    }

    @PostMapping("/cluster/instances/purge")
    public R<Map<String, Object>> purgeInstances(
            @RequestParam(value = "offlineOnly", defaultValue = "true") boolean offlineOnly) {
        int removed = clusterControlService.purgeStaleInstances(offlineOnly);
        return R.ok(Map.of(
                "removed", removed,
                "instances", clusterControlService.listInstances()
        ));
    }

    @DeleteMapping("/cluster/instances/{instanceId}")
    public R<Boolean> removeInstance(@PathVariable String instanceId) {
        try {
            return R.ok(clusterControlService.removeInstanceRecord(instanceId));
        } catch (IllegalArgumentException e) {
            return R.fail(e.getMessage());
        }
    }

    @PostMapping("/cluster/command")
    public R<Map<String, String>> issueCommand(@RequestBody TransformCommand command) {
        String id = clusterControlService.issueCommand(command);
        return R.ok(Map.of("commandId", id));
    }

    @GetMapping("/cluster/command/{commandId}/acks")
    public R<List<TransformCommandAck>> commandAcks(@PathVariable String commandId) {
        return R.ok(clusterControlService.listCommandAcks(commandId));
    }

    // ---- Party ----
    @GetMapping("/party")
    public R<Collection<Party>> listParties() {
        return R.ok(repository.listParties());
    }

    @GetMapping("/party/{id}")
    public R<Party> getParty(@PathVariable String id) {
        Party party = repository.party(id);
        return party == null ? R.fail("not found") : R.ok(party);
    }

    @PostMapping("/party")
    public R<Party> createParty(@RequestBody Party party) {
        return R.ok(repository.save(party));
    }

    @PutMapping("/party/{id}")
    public R<Party> updateParty(@PathVariable String id, @RequestBody Party party) {
        party.setId(id);
        return R.ok(repository.save(party));
    }

    @DeleteMapping("/party/{id}")
    public R<Void> deleteParty(@PathVariable String id) {
        repository.deleteParty(id);
        return R.ok(null);
    }

    // ---- Contract ----
    @GetMapping("/contract")
    public R<Collection<Contract>> listContracts() {
        return R.ok(repository.listContracts());
    }

    @PostMapping("/contract")
    public R<Contract> createContract(@RequestBody Contract contract) {
        return R.ok(repository.save(contract));
    }

    @PutMapping("/contract/{id}")
    public R<Contract> updateContract(@PathVariable String id, @RequestBody Contract contract) {
        contract.setId(id);
        return R.ok(repository.save(contract));
    }

    @DeleteMapping("/contract/{id}")
    public R<Void> deleteContract(@PathVariable String id) {
        repository.deleteContract(id);
        return R.ok(null);
    }

    // ---- Mapping ----
    @GetMapping("/mapping")
    public R<Collection<MappingRule>> listMappings() {
        return R.ok(repository.listMappings());
    }

    @PostMapping("/mapping")
    public R<MappingRule> createMapping(@RequestBody MappingRule rule) {
        return R.ok(repository.save(rule));
    }

    @PutMapping("/mapping/{id}")
    public R<MappingRule> updateMapping(@PathVariable String id, @RequestBody MappingRule rule) {
        rule.setId(id);
        return R.ok(repository.save(rule));
    }

    @DeleteMapping("/mapping/{id}")
    public R<Void> deleteMapping(@PathVariable String id) {
        repository.deleteMapping(id);
        return R.ok(null);
    }

    // ---- Pipeline ----
    @GetMapping("/pipeline")
    public R<Collection<PipelineDef>> listPipelines() {
        return R.ok(repository.listPipelines());
    }

    @PostMapping("/pipeline")
    public R<PipelineDef> createPipeline(@RequestBody PipelineDef pipelineDef) {
        return R.ok(repository.save(pipelineDef));
    }

    @PutMapping("/pipeline/{id}")
    public R<PipelineDef> updatePipeline(@PathVariable String id, @RequestBody PipelineDef pipelineDef) {
        pipelineDef.setId(id);
        return R.ok(repository.save(pipelineDef));
    }

    @PostMapping("/pipeline/{id}/enable")
    public R<PipelineDef> enablePipeline(@PathVariable String id, @RequestParam boolean enabled) {
        PipelineDef pipelineDef = repository.listPipelines().stream().filter(p -> id.equals(p.getId())).findFirst().orElse(null);
        if (pipelineDef == null) {
            return R.fail("not found");
        }
        pipelineDef.setEnabled(enabled);
        return R.ok(repository.save(pipelineDef));
    }

    @DeleteMapping("/pipeline/{id}")
    public R<Void> deletePipeline(@PathVariable String id) {
        repository.deletePipeline(id);
        return R.ok(null);
    }

    // ---- Outbox / DLQ / Backup ----
    @GetMapping("/outbox")
    public R<Collection<OutboxRecord>> listOutbox() {
        return R.ok(repository.listOutbox());
    }

    @PostMapping("/outbox/{id}/replay")
    public R<Void> replayOutbox(@PathVariable String id) {
        try {
            pipeline.replayOutbox(id);
            return R.ok(null);
        } catch (Exception e) {
            return R.fail(e.getMessage());
        }
    }

    @GetMapping("/dlq")
    public R<Collection<DlqRecord>> listDlq() {
        return R.ok(repository.listDlq());
    }

    @PostMapping("/dlq/{id}/replay")
    public R<Void> replayDlq(@PathVariable String id) {
        try {
            pipeline.replay(id);
            return R.ok(null);
        } catch (Exception e) {
            return R.fail(e.getMessage());
        }
    }

    @GetMapping("/backup")
    public R<Map<String, Object>> backupInfo() {
        return R.ok(Map.of(
                "mode", "file",
                "note", "archives written under transform.backup-dir on accept"
        ));
    }
}
