package com.basiclab.iot.video.controller;



import com.basiclab.iot.video.domain.vo.VideoApiResponse;

import com.basiclab.iot.video.service.PlateMatchingService;

import lombok.RequiredArgsConstructor;

import org.springframework.web.bind.annotation.PostMapping;

import org.springframework.web.bind.annotation.RequestBody;

import org.springframework.web.bind.annotation.RequestMapping;

import org.springframework.web.bind.annotation.RestController;



import java.util.Map;



@RestController

@RequestMapping("/video/plate/matching")

@RequiredArgsConstructor

public class PlateMatchingController {



    private final PlateMatchingService plateMatchingService;



    @PostMapping("/publish")

    public VideoApiResponse<Map<String, Object>> publish(@RequestBody(required = false) Map<String, Object> body) {

        Map<String, Object> message = plateMatchingService.publish(body);

        return VideoApiResponse.success("投递成功", message);

    }



    @PostMapping("/process")

    public VideoApiResponse<Map<String, Object>> process(@RequestBody(required = false) Map<String, Object> body) {

        Map<String, Object> record = plateMatchingService.process(body);

        return VideoApiResponse.success("处理成功", record);

    }

}

