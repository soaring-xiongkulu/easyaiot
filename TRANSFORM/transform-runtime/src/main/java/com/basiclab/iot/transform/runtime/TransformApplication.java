package com.basiclab.iot.transform.runtime;

import com.basiclab.iot.transform.capability.sense.DefaultSenseCapability;
import com.basiclab.iot.transform.capability.sense.SenseCapability;
import com.basiclab.iot.transform.channel.http.HttpDeliverChannel;
import com.basiclab.iot.transform.channel.jdbc.JdbcChannel;
import com.basiclab.iot.transform.channel.kafka.KafkaIngressChannel;
import com.basiclab.iot.transform.channel.mqtt.MqttDeliverChannel;
import com.basiclab.iot.transform.channel.party.PartyDeliverChannel;
import com.basiclab.iot.transform.channel.party.MesRestPartyConnector;
import com.basiclab.iot.transform.channel.party.ErpRestPartyConnector;
import com.basiclab.iot.transform.channel.party.WmsRestPartyConnector;
import com.basiclab.iot.transform.core.spi.PartyConnector;
import com.basiclab.iot.transform.core.spi.TransformChannel;
import com.basiclab.iot.transform.capability.backup.BackupCapability;
import com.basiclab.iot.transform.capability.backup.FileBackupCapability;
import com.basiclab.iot.transform.runtime.config.TransformRuntimeProperties;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.kafka.annotation.EnableKafka;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.mybatis.spring.annotation.MapperScan;
import com.alibaba.druid.spring.boot.autoconfigure.DruidDataSourceAutoConfigure;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

import java.util.ArrayList;
import java.util.List;
import java.net.http.HttpClient;
import java.time.Duration;

/**
 * TRANSFORM 运行时入口。
 * <p>
 * 同一套制品可在任意节点启动；按配置启用渠道并自动 join 约定 Group，
 * 从而扩展全集群消费与投递能力。进程无本地权威状态，可随时销毁重建。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@EnableKafka
@SpringBootApplication(scanBasePackages = "com.basiclab.iot.transform", exclude = DruidDataSourceAutoConfigure.class)
@EnableConfigurationProperties(TransformRuntimeProperties.class)
@EnableScheduling
@EnableDiscoveryClient
@MapperScan("com.basiclab.iot.transform.runtime.dal.mapper")
public class TransformApplication {

    public static void main(String[] args) {
        // 保证 Kafka command Group 在监听器创建前就有稳定 instance-id
        String envId = System.getenv("TRANSFORM_INSTANCE_ID");
        String propId = System.getProperty("transform.instance-id");
        if ((envId == null || envId.isBlank()) && (propId == null || propId.isBlank())) {
            System.setProperty("transform.instance-id",
                    java.util.UUID.randomUUID().toString().replace("-", ""));
        } else if (propId == null || propId.isBlank()) {
            System.setProperty("transform.instance-id", envId);
        }
        SpringApplication.run(TransformApplication.class, args);
    }

    @Bean
    public ObjectMapper transformObjectMapper() {
        return new ObjectMapper().findAndRegisterModules();
    }

    @Bean
    public HttpClient transformHttpClient() {
        return HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
    }

    @Bean
    public BackupCapability backupCapability(TransformRuntimeProperties properties, ObjectMapper transformObjectMapper) {
        return new FileBackupCapability(properties.getBackupDir(), transformObjectMapper);
    }

    @Bean
    public List<PartyConnector> partyConnectors(HttpClient transformHttpClient, ObjectMapper transformObjectMapper) {
        return List.of(new MesRestPartyConnector(transformHttpClient, transformObjectMapper),
                new ErpRestPartyConnector(transformHttpClient, transformObjectMapper),
                new WmsRestPartyConnector(transformHttpClient, transformObjectMapper));
    }

    @Bean
    public SenseCapability senseCapability(TransformRuntimeProperties properties) {
        String id = properties.getInstanceId();
        if (id == null || id.isBlank()) {
            DefaultSenseCapability capability = new DefaultSenseCapability();
            properties.setInstanceId(capability.getInstanceId());
            return capability;
        }
        return new DefaultSenseCapability(id);
    }

    @Bean
    public List<TransformChannel> transformChannels(TransformRuntimeProperties properties,
                                                    ObjectMapper transformObjectMapper,
                                                    HttpClient transformHttpClient,
                                                    List<PartyConnector> partyConnectors) {
        List<TransformChannel> channels = new ArrayList<>();
        if (properties.getChannels().isKafka() && !"edge".equalsIgnoreCase(properties.getRole())) {
            channels.add(new KafkaIngressChannel(transformObjectMapper));
        }
        if (properties.getChannels().isHttp()) {
            channels.add(new HttpDeliverChannel(transformHttpClient, transformObjectMapper,
                    Duration.ofMillis(properties.getHttp().getTimeoutMs())));
        }
        if (properties.getChannels().isMqtt()) {
            channels.add(new MqttDeliverChannel());
        }
        if (properties.getChannels().isJdbc()) {
            channels.add(new JdbcChannel());
        }
        if (properties.getChannels().isParty()) {
            channels.add(new PartyDeliverChannel(partyConnectors));
        }
        log.info("[TransformApplication] enabled channels={}",
                channels.stream().map(c -> c.type().code()).toList());
        return channels;
    }
}
