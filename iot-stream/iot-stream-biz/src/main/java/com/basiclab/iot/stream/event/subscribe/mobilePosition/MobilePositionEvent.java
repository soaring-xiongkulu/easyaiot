package com.basiclab.iot.stream.event.subscribe.mobilePosition;

import com.basiclab.iot.stream.bean.MobilePosition;
import lombok.Getter;
import lombok.Setter;
import org.springframework.context.ApplicationEvent;


public class MobilePositionEvent extends ApplicationEvent {
    public MobilePositionEvent(Object source) {
        super(source);
    }

    @Getter
    @Setter
    private MobilePosition mobilePosition;
}
