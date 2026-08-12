namespace EasyAIoT.Edge.Abstractions.Config;

/// <summary>
/// 边缘采集任务配置（本地文件或云端 MQTT 下发）。
/// </summary>
public sealed class DeviceJobConfig
{
    public string JobId { get; set; } = Guid.NewGuid().ToString("N");

    public string DeviceIdentification { get; set; } = "";

    public string? SubDeviceIdentification { get; set; }

    /// <summary>子设备所属产品（SUBSET 产品标识），网关代报时必填。</summary>
    public string? SubProductIdentification { get; set; }

    public string CollectorId { get; set; } = "modbus-rtu";

    public string AgreementType { get; set; } = "rs485";

    public bool Enabled { get; set; } = true;

    public int IntervalSeconds { get; set; } = 30;

    public ConnectionConfig Connection { get; set; } = new();

    public List<PointConfig> Points { get; set; } = new();
}
