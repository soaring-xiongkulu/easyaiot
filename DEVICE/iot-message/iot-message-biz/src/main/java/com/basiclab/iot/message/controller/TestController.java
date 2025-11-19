package com.basiclab.iot.message.controller;


import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/test")
public class TestController {

    @GetMapping("/test01")
    public String test(){
        System.out.println("hello world");
        return "hello world!!!";
    }
}
