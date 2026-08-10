package com.basiclab.iot.video.service.camera.hardware;

import lombok.extern.slf4j.Slf4j;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.NetworkInterface;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
public final class OnvifWsDiscovery {

    private static final String MULTICAST_ADDRESS = "239.255.255.250";
    private static final int MULTICAST_PORT = 3702;
    private static final Pattern IP_PATTERN = Pattern.compile("(\\d+\\.\\d+\\.\\d+\\.\\d+)");

    public List<Map<String, Object>> discover(int timeoutMs) {
        List<Map<String, Object>> devices = new ArrayList<>();
        String probe = """
                <?xml version="1.0" encoding="UTF-8"?>
                <e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope"
                            xmlns:w="http://schemas.xmlsoap.org/ws/2004/08/addressing"
                            xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
                            xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
                  <e:Header>
                    <w:MessageID>uuid:%s</w:MessageID>
                    <w:To e:mustUnderstand="true">urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To>
                    <w:Action a:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</w:Action>
                  </e:Header>
                  <e:Body>
                    <d:Probe>
                      <d:Types>dn:NetworkVideoTransmitter</d:Types>
                    </d:Probe>
                  </e:Body>
                </e:Envelope>
                """.formatted(java.util.UUID.randomUUID());
        byte[] data = probe.getBytes(StandardCharsets.UTF_8);
        try (DatagramSocket socket = new DatagramSocket()) {
            socket.setSoTimeout(Math.max(500, timeoutMs));
            socket.setBroadcast(true);
            for (InetAddress iface : localAddresses()) {
                try {
                    socket.send(new DatagramPacket(data, data.length, new InetSocketAddress(MULTICAST_ADDRESS, MULTICAST_PORT)));
                } catch (Exception ex) {
                    log.debug("WS-Discovery send on {} failed: {}", iface, ex.getMessage());
                }
            }
            long deadline = System.currentTimeMillis() + timeoutMs;
            byte[] buffer = new byte[8192];
            while (System.currentTimeMillis() < deadline) {
                try {
                    DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                    socket.receive(packet);
                    String response = new String(packet.getData(), 0, packet.getLength(), StandardCharsets.UTF_8);
                    Map<String, Object> row = parseProbeMatch(response);
                    if (row != null && row.get("ip") != null) {
                        if (devices.stream().noneMatch(d -> row.get("ip").equals(d.get("ip")))) {
                            devices.add(row);
                        }
                    }
                } catch (Exception ex) {
                    break;
                }
            }
        } catch (Exception ex) {
            log.warn("WS-Discovery failed: {}", ex.getMessage());
        }
        return devices;
    }

    private static Map<String, Object> parseProbeMatch(String xml) {
        String xaddrs = extractTag(xml, "XAddrs");
        if (xaddrs == null || xaddrs.isBlank()) {
            return null;
        }
        Matcher ipMatcher = IP_PATTERN.matcher(xaddrs);
        if (!ipMatcher.find()) {
            return null;
        }
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("ip", ipMatcher.group(1));
        String mac = null;
        for (String scope : xml.split("\\s+")) {
            if (scope.contains("onvif://www.onvif.org/MAC/")) {
                mac = scope.substring(scope.lastIndexOf('/') + 1);
            }
        }
        row.put("mac", mac);
        String name = null;
        Matcher nameMatcher = Pattern.compile("onvif://www\\.onvif\\.org/name/([^\\s]+)").matcher(xml);
        if (nameMatcher.find()) {
            name = nameMatcher.group(1);
        }
        row.put("hardware_name", name);
        return row;
    }

    private static String extractTag(String xml, String tag) {
        Matcher matcher = Pattern.compile("<(?:[\\w-]+:)?" + tag + ">([^<]+)</(?:[\\w-]+:)?" + tag + ">", Pattern.CASE_INSENSITIVE)
                .matcher(xml);
        return matcher.find() ? matcher.group(1).trim() : null;
    }

    private static List<InetAddress> localAddresses() {
        List<InetAddress> addresses = new ArrayList<>();
        try {
            Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
            while (interfaces.hasMoreElements()) {
                NetworkInterface networkInterface = interfaces.nextElement();
                if (!networkInterface.isUp() || networkInterface.isLoopback()) {
                    continue;
                }
                Enumeration<InetAddress> inetAddresses = networkInterface.getInetAddresses();
                while (inetAddresses.hasMoreElements()) {
                    InetAddress address = inetAddresses.nextElement();
                    if (address instanceof java.net.Inet4Address) {
                        addresses.add(address);
                    }
                }
            }
        } catch (Exception ignored) {
        }
        if (addresses.isEmpty()) {
            try {
                addresses.add(InetAddress.getByName("0.0.0.0"));
            } catch (Exception ignored) {
            }
        }
        return addresses;
    }
}
