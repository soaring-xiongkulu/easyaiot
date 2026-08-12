namespace EasyAIoT.Edge.Abstractions.Config;

public sealed class ConnectionConfig
{
    public string PortName { get; set; } = "/dev/ttyS3";

    public int BaudRate { get; set; } = 9600;

    public string? Host { get; set; }

    public int Port { get; set; } = 502;

    public int SlaveId { get; set; } = 1;

    /// <summary>OPC UA 端点，例如 opc.tcp://127.0.0.1:4840。</summary>
    public string? EndpointUrl { get; set; }

    public string? Username { get; set; }

    public string? Password { get; set; }
}
