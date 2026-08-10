package com.basiclab.iot.video.config;

import com.basiclab.iot.video.util.FfmpegCompat;
import javax.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class FfmpegPathBootstrap {

    private final VideoProperties videoProperties;

    @PostConstruct
    public void applyConfiguredPath() {
        String configured = videoProperties.getFfmpegPath();
        if (configured != null && !configured.isBlank()) {
            FfmpegCompat.setConfiguredBinary(configured.trim());
        }
    }
}
