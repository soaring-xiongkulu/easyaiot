package com.basiclab.iot.node.util;

import java.net.DatagramSocket;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.util.Enumeration;

/**
 * 探测平台宿主机可用 IPv4（供 Agent 平台接入地址等场景使用）。
 */
public final class HostIpUtil {

    private static volatile String cachedHostIp;

    private HostIpUtil() {
    }

    public static String detectHostIp() {
        if (cachedHostIp != null) {
            return cachedHostIp;
        }
        String envHost = System.getenv("EASYAIOT_PLATFORM_HOST");
        if (envHost != null && !envHost.isBlank() && isUsableIpv4(envHost.trim())) {
            cachedHostIp = envHost.trim();
            return cachedHostIp;
        }
        String ip = detectViaUdp();
        if (ip == null) {
            ip = detectViaNetworkInterfaces();
        }
        if (ip != null) {
            cachedHostIp = ip;
            return ip;
        }
        return "127.0.0.1";
    }

    private static String detectViaUdp() {
        try (DatagramSocket socket = new DatagramSocket()) {
            socket.connect(InetAddress.getByName("8.8.8.8"), 80);
            String ip = socket.getLocalAddress().getHostAddress();
            if (isUsableIpv4(ip)) {
                return ip;
            }
        } catch (Exception ignored) {
            // ignore
        }
        return null;
    }

    private static String detectViaNetworkInterfaces() {
        try {
            Enumeration<NetworkInterface> nifs = NetworkInterface.getNetworkInterfaces();
            while (nifs.hasMoreElements()) {
                NetworkInterface nif = nifs.nextElement();
                if (!nif.isUp() || nif.isLoopback() || isVirtualInterface(nif.getName())) {
                    continue;
                }
                Enumeration<InetAddress> addresses = nif.getInetAddresses();
                while (addresses.hasMoreElements()) {
                    InetAddress addr = addresses.nextElement();
                    if (addr instanceof Inet4Address) {
                        String hostAddress = addr.getHostAddress();
                        if (isUsableIpv4(hostAddress)) {
                            return hostAddress;
                        }
                    }
                }
            }
        } catch (Exception ignored) {
            // ignore
        }
        return null;
    }

    private static boolean isVirtualInterface(String name) {
        return name.startsWith("docker")
                || name.startsWith("br-")
                || name.startsWith("veth")
                || name.startsWith("virbr");
    }

    private static boolean isUsableIpv4(String ip) {
        return ip != null
                && !ip.isEmpty()
                && !"127.0.0.1".equals(ip)
                && !ip.startsWith("169.254.");
    }
}
