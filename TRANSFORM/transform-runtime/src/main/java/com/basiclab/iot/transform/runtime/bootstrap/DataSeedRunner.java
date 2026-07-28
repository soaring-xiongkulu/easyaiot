package com.basiclab.iot.transform.runtime.bootstrap;

import com.basiclab.iot.transform.core.domain.*;
import com.basiclab.iot.transform.runtime.dal.TransformRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

import java.util.HashMap;

/** Seeds demo data only when the schema has no parties. */
@Component
@RequiredArgsConstructor
public class DataSeedRunner implements ApplicationRunner {
    private final TransformRepository repository;
    @Override public void run(ApplicationArguments args) {
        if (repository.partyCount() > 0) return;
        Party mes = repository.save(Party.builder().id("demo-mes").name("Demo MES").type("mes.rest").enabled(true).config(new HashMap<>()).build());
        Party erp = repository.save(Party.builder().id("demo-erp").name("Demo ERP").type("erp.rest").enabled(true).config(new HashMap<>()).build());
        repository.save(Party.builder().id("demo-wms").name("Demo WMS").type("wms.rest").enabled(true).config(new HashMap<>()).build());
        MappingRule identity = repository.save(MappingRule.builder().id("map-identity").name("identity").fields(new HashMap<>()).enabled(true).build());
        repository.save(Contract.builder().id("contract-mes-alert").partyId(mes.getId()).flowType("ALERT").channel("party").endpoint("http://127.0.0.1:18080/mes/alerts").mappingId(identity.getId()).enabled(true).build());
        repository.save(Contract.builder().id("contract-erp-data").partyId(erp.getId()).flowType("DATA").channel("party").endpoint("http://127.0.0.1:18080/erp/telemetry").mappingId(identity.getId()).enabled(true).build());
        repository.save(Contract.builder().id("contract-http-webhook").partyId(mes.getId()).channel("http").endpoint("http://127.0.0.1:18080/webhook/transform").enabled(false).build());
        repository.save(PipelineDef.builder().id("pipeline-default").name("default").mappingId(identity.getId()).enabled(true).build());
    }
}
