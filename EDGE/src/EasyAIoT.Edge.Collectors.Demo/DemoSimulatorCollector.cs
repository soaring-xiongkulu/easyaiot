using EasyAIoT.Edge.Abstractions.Collectors;
using Microsoft.Extensions.Logging;

namespace EasyAIoT.Edge.Collectors.Demo;

/// <summary>
/// 联调/demo 用采集器：不依赖现场设备，周期性生成模拟测点。
/// </summary>
public sealed class DemoSimulatorCollector : ICollector
{
    private ILogger? _logger;
    private int _tick;

    public string CollectorId => "demo-simulator";

    public IReadOnlyList<string> SupportedAgreementTypes => new[] { "demo" };

    public Task InitializeAsync(CollectorContext context, CancellationToken cancellationToken = default)
    {
        _logger = context.Logger;
        return Task.CompletedTask;
    }

    public Task<CollectResult> CollectAsync(CollectRequest request, CancellationToken cancellationToken = default)
    {
        _tick++;
        var rnd = Random.Shared;
        var variables = new Dictionary<string, object>
        {
            ["temperature"] = Math.Round(20 + rnd.NextDouble() * 10, 2),
            ["humidity"] = Math.Round(40 + rnd.NextDouble() * 30, 2),
            ["pressure"] = Math.Round(100 + rnd.NextDouble() * 5, 2),
            ["tick"] = _tick,
            ["deviceId"] = request.DeviceId,
            ["collectorId"] = CollectorId
        };

        _logger?.LogDebug("Demo collect job={JobId} tick={Tick}", request.JobId, _tick);
        return Task.FromResult(CollectResult.Ok(variables));
    }

    public Task<WriteResult> WriteAsync(Abstractions.Collectors.WriteRequest request, CancellationToken cancellationToken = default)
    {
        _logger?.LogInformation("Demo write accepted keys={Keys}", string.Join(",", request.Values.Keys));
        return Task.FromResult(WriteResult.Ok());
    }

    public Task StopAsync(CancellationToken cancellationToken = default) => Task.CompletedTask;
}
