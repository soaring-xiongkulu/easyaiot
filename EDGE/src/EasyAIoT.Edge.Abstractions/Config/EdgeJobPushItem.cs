namespace EasyAIoT.Edge.Abstractions.Config;

/// <summary>
/// 云端下发的单条边缘任务（protocolConfig + 设备元数据）。
/// </summary>
public sealed class EdgeJobPushItem
{
    public string? JobId { get; set; }

    public string? DeviceIdentification { get; set; }

    public string? SubDeviceIdentification { get; set; }

    public string? SubProductIdentification { get; set; }

    public string? CollectorId { get; set; }

    public string? AgreementType { get; set; }

    public bool? Enabled { get; set; }

    public int? IntervalSeconds { get; set; }

  /// <summary>与 iot-sink IndustrialDeviceConfig 同构。</summary>
    public IndustrialProtocolConfig? ProtocolConfig { get; set; }
}
