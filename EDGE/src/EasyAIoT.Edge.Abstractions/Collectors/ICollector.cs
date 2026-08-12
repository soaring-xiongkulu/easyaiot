namespace EasyAIoT.Edge.Abstractions.Collectors;

/// <summary>
/// 协议采集器插件接口。每种协议/厂家可实现独立 C# 采集器并注册到 <see cref="ICollectorRegistry"/>。
/// </summary>
public interface ICollector
{
    /// <summary>采集器唯一标识，如 modbus-rtu、opc-ua。</summary>
    string CollectorId { get; }

    /// <summary>支持的协议类型标签，如 rs485、tcp。</summary>
    IReadOnlyList<string> SupportedAgreementTypes { get; }

    Task InitializeAsync(CollectorContext context, CancellationToken cancellationToken = default);

    Task<CollectResult> CollectAsync(CollectRequest request, CancellationToken cancellationToken = default);

    Task<WriteResult> WriteAsync(WriteRequest request, CancellationToken cancellationToken = default);

    Task StopAsync(CancellationToken cancellationToken = default);
}
