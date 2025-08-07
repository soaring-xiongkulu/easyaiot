package com.basiclab.iot.stream.web;

import com.basiclab.iot.stream.service.IUserService;
import com.basiclab.iot.stream.storager.dto.User;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;


@RestController
@RequestMapping(value = "/auth")
public class AuthController {

    @Autowired
    private IUserService userService;

    @GetMapping("/login")
    public String devices(String name, String passwd){
        User user = userService.getUser(name, passwd);
        if (user != null) {
            return "success";
        }else {
            return "fail";
        }
    }
}
