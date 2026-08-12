namespace EasyAIoT.Edge.Abstractions.Config;

public sealed class PointConfig
{
    public string Key { get; set; } = "";

    public string Name { get; set; } = "";

    /// <summary>Modbus 功能码：1/2/3/4。</summary>
    public int Function { get; set; } = 3;

    public int Address { get; set; }

    public int Length { get; set; } = 1;

    /// <summary>自定义 hex 帧，优先于 Function/Address。</summary>
    public string? HexFrame { get; set; }

    /// <summary>OPC UA 节点 ID，例如 ns=2;s=Temperature。</summary>
    public string? NodeId { get; set; }

    public ParseRule Parse { get; set; } = new();
}
