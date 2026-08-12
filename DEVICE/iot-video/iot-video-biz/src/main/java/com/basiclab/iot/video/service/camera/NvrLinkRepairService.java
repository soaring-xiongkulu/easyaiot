package com.basiclab.iot.video.service.camera;

import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.dal.NvrRepository;
import com.basiclab.iot.video.domain.DeviceRow;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Mirrors Python {@code repair_nvr_channel_links}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class NvrLinkRepairService {

    private static final Pattern HIK_CHANNEL = Pattern.compile("/Streaming/Channels/(\\d+)", Pattern.CASE_INSENSITIVE);
    private static final Pattern DAHUA_CHANNEL = Pattern.compile("[?&]channel=(\\d+)", Pattern.CASE_INSENSITIVE);

    private final DeviceRepository deviceRepository;
    private final NvrRepository nvrRepository;

    public int repairNvrChannelLinks() {
        Map<String, Integer> nvrByIp = nvrRepository.buildIpIndex();
        List<DeviceRow> candidates = deviceRepository.listNvrChannelCandidatesWithoutNvrId();
        int fixed = 0;
        for (DeviceRow cam : candidates) {
            NvrLink link = inferNvrLinkFromSource(cam.getSource(), nvrByIp);
            if (link.nvrId() == null) {
                continue;
            }
            java.util.Map<String, Object> fields = new java.util.LinkedHashMap<>();
            fields.put("nvr_id", link.nvrId());
            if (link.channel() > 0 && cam.getNvrChannel() <= 0) {
                fields.put("nvr_channel", link.channel());
            }
            deviceRepository.updateFields(cam.getId(), fields);
            fixed++;
        }
        if (fixed > 0) {
            log.info("已修复 {} 条 NVR 通道的 nvr_id 关联", fixed);
        }
        return fixed;
    }

    static NvrLink inferNvrLinkFromSource(String source, Map<String, Integer> nvrByIp) {
        String text = source != null ? source.strip() : "";
        if (!text.toLowerCase().startsWith("rtsp://")) {
            return new NvrLink(null, 0);
        }
        try {
            String host = URI.create(text).getHost();
            if (host == null || host.isBlank()) {
                return new NvrLink(null, 0);
            }
            Integer nvrId = nvrByIp.get(host.strip());
            if (nvrId == null) {
                return new NvrLink(null, 0);
            }
            int channel = 0;
            Matcher hik = HIK_CHANNEL.matcher(text);
            if (hik.find()) {
                int streamId = Integer.parseInt(hik.group(1));
                channel = streamId >= 100 ? streamId / 100 : streamId;
            } else {
                Matcher dh = DAHUA_CHANNEL.matcher(text);
                if (dh.find()) {
                    channel = Integer.parseInt(dh.group(1));
                }
            }
            return new NvrLink(nvrId, channel);
        } catch (Exception ex) {
            return new NvrLink(null, 0);
        }
    }

    record NvrLink(Integer nvrId, int channel) {
    }
}
