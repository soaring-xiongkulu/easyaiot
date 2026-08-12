namespace EasyAIoT.Edge.Mqtt.Options;

public sealed class EdgeGatewayOptions
{
    public const string SectionName = "Edge:Gateway";

    public string ProductIdentification { get; set; } = "edge-gateway";

    public string DeviceIdentification { get; set; } = "gateway-001";
}

public sealed class EdgeMqttOptions
{
    public const string SectionName = "Edge:Mqtt";

    public string Host { get; set; } = "127.0.0.1";

    public int Port { get; set; } = 1883;

    public string? Username { get; set; }

    public string? Password { get; set; }

    public string? ClientId { get; set; }

    public bool UseTls { get; set; } = false;
}
