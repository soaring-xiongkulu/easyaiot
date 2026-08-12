using System.Text.Json.Serialization;

namespace EasyAIoT.Edge.Mqtt.Messages;

/// <summary>
/// 对齐 iot-sink IotDeviceMessage 最小字段集。
/// </summary>
public sealed class IotDeviceMessage
{
    [JsonPropertyName("id")]
    public string? Id { get; set; }

    [JsonPropertyName("method")]
    public string? Method { get; set; }

    [JsonPropertyName("params")]
    public Dictionary<string, object>? Params { get; set; }

    [JsonPropertyName("code")]
    public int? Code { get; set; }

    [JsonPropertyName("msg")]
    public string? Msg { get; set; }

    public static IotDeviceMessage PropertyPost(Dictionary<string, object> properties) =>
        new()
        {
            Id = Guid.NewGuid().ToString("N"),
            Method = "thing.event.property.post",
            Params = properties
        };

    public static IotDeviceMessage PropertySetAck(bool success, string message) =>
        new()
        {
            Id = Guid.NewGuid().ToString("N"),
            Method = "thing.service.property.set",
            Code = success ? 0 : 1,
            Msg = message
        };
}
