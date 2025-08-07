
package com.basiclab.iot.things;

import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.*;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.codec.mqtt.MqttDecoder;
import io.netty.handler.codec.mqtt.MqttEncoder;
import io.netty.handler.codec.mqtt.MqttMessageType;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@Slf4j
public class MqttServer {

    MqttServer mqttServer;

    @Getter
    private final List<MqttMessageType> eventsFromClient = new CopyOnWriteArrayList<>();
    @Getter
    private final int mqttPort = 8885;

    private Channel serverChannel;
    private EventLoopGroup bossGroup;
    private EventLoopGroup workerGroup;

    public void init() throws Exception {
        log.info("Starting MQTT server...");
        bossGroup = new NioEventLoopGroup();
        workerGroup = new NioEventLoopGroup();
        ServerBootstrap b = new ServerBootstrap();
        b.group(bossGroup, workerGroup)
                .channel(NioServerSocketChannel.class)
                .childHandler(new ChannelInitializer<SocketChannel>() {
                    @Override
                    protected void initChannel(SocketChannel ch) throws Exception {
                        ChannelPipeline pipeline = ch.pipeline();
                        pipeline.addLast("decoder", new MqttDecoder(65536));
                        pipeline.addLast("encoder", MqttEncoder.INSTANCE);

                        MqttTransportHandler handler = new MqttTransportHandler(eventsFromClient);

                        pipeline.addLast(handler);
                        ch.closeFuture().addListener(handler);
                    }
                })
                .childOption(ChannelOption.SO_KEEPALIVE, true);

        serverChannel = b.bind(mqttPort).sync().channel();
        log.info("Mqtt transport started!");
    }

    public void shutdown() throws InterruptedException {
        log.info("Stopping MQTT transport!");
        try {
            serverChannel.close().sync();
        } finally {
            workerGroup.shutdownGracefully();
            bossGroup.shutdownGracefully();
        }
        log.info("MQTT transport stopped!");
    }

    public static void main(String[] args) {
        try {
            MqttServer mqttServer = new MqttServer();
            mqttServer.init();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
