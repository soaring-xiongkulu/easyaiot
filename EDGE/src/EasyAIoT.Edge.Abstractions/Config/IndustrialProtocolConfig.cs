namespace EasyAIoT.Edge.Abstractions.Config;

/// <summary>
/// 与 DEVICE 模块 IndustrialDeviceConfig 字段对齐的协议配置。
/// </summary>
public sealed class IndustrialProtocolConfig
{
    public string? Type { get; set; }

    public bool? Enabled { get; set; }

    public string? Host { get; set; }

    public int? Port { get; set; }

    public int? UnitId { get; set; }

    public string? SerialPort { get; set; }

    public int? BaudRate { get; set; }

    public string? EndpointUrl { get; set; }

    public string? Username { get; set; }

    public string? Password { get; set; }

    public long? PollIntervalMs { get; set; }

    public List<IndustrialPointConfig> Points { get; set; } = new();
}

public sealed class IndustrialPointConfig
{
    public string? PropertyCode { get; set; }

    public string? Identifier { get; set; }

    public string? Function { get; set; }

    public int? Address { get; set; }

    public int? Quantity { get; set; }

    public string? DataType { get; set; }

    public double? Scale { get; set; }

    public double? Offset { get; set; }

    public string? NodeId { get; set; }

    public bool? Writable { get; set; }

    public string ResolvedPropertyCode() =>
        string.IsNullOrWhiteSpace(PropertyCode) ? Identifier ?? "" : PropertyCode;
}
