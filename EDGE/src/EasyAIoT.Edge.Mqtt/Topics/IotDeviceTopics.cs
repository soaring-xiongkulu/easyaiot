namespace EasyAIoT.Edge.Mqtt.Topics;

/// <summary>
/// 对齐 DEVICE/iot-sink IotDeviceTopicEnum 的 Topic 构建。
/// </summary>
public static class IotDeviceTopics
{
    public static string PropertyUpstreamReport(string productIdentification, string deviceIdentification) =>
        $"/iot/{productIdentification}/{deviceIdentification}/property/upstream/report";

    public static string SubPropertyUpstreamReport(string productIdentification, string gatewayIdentification) =>
        $"/iot/{productIdentification}/{gatewayIdentification}/sub/property/upstream/report";

    public static string ConfigDownstreamPush(string productIdentification, string deviceIdentification) =>
        $"/iot/{productIdentification}/{deviceIdentification}/config/downstream/push";

    public static string PropertyDownstreamDesiredSet(string productIdentification, string deviceIdentification) =>
        $"/iot/{productIdentification}/{deviceIdentification}/property/downstream/desired/set";

    public static string SubPropertyDownstreamDesiredSet(string productIdentification, string gatewayIdentification) =>
        $"/iot/{productIdentification}/{gatewayIdentification}/sub/property/downstream/desired/set";

    public static string PropertyUpstreamDesiredSetAck(string productIdentification, string deviceIdentification) =>
        $"/iot/{productIdentification}/{deviceIdentification}/property/upstream/desired/set/ack";

    public static string NtpUpstreamRequest(string productIdentification, string deviceIdentification) =>
        $"/iot/{productIdentification}/{deviceIdentification}/ntp/upstream/request";
}
