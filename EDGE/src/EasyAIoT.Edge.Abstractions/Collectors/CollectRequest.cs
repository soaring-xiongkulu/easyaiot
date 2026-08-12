namespace EasyAIoT.Edge.Abstractions.Collectors;

public sealed class CollectRequest
{
  public required string JobId { get; init; }

  public required string DeviceId { get; init; }

  /// <summary>子设备标识；网关代报时使用。</summary>
  public string? SubDeviceIdentification { get; init; }

  public required string CollectorId { get; init; }

  public string? CommandKey { get; init; }

  /// <summary>连接参数 JSON（端口、波特率、IP 等）。</summary>
  public required string ConnectionJson { get; init; }

  /// <summary>点表/解析规则 JSON。</summary>
  public required string PointConfigJson { get; init; }
}
