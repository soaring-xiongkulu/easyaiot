package com.basiclab.iot.rule.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.rule.domain.AlarmRecord;
import com.basiclab.iot.rule.mapper.AlarmRecordMapper;
import com.basiclab.iot.rule.service.AlarmRecordService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

/**
 * @author IoT
 * @desc
 * @created 2024-07-18
 */
@Slf4j
@Service
public class AlarmRecordServiceImpl extends ServiceImpl<AlarmRecordMapper, AlarmRecord> implements AlarmRecordService {
}
