using EasyAIoT.Edge.Core.Config;
using System.Text.Json;
using EasyAIoT.Edge.Abstractions.Config;
using EasyAIoT.Edge.Abstractions.Collectors;
using EasyAIoT.Edge.Mqtt.Client;
using EasyAIoT.Edge.Mqtt.Topics;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace EasyAIoT.Edge.Core.Hosting;

/// <summary>
/// 边缘运行时：MQTT 下行配置 + 本地调度采集 + 结构化上报。
/// </summary>
public sealed class EdgeRuntimeService : BackgroundService
{
    private readonly ILogger<EdgeRuntimeService> _logger;
    private readonly IDeviceJobStore _jobStore;
    private readonly ICollectorRegistry _registry;
    private readonly MqttEdgeClient _mqtt;
    private readonly IServiceProvider _services;
    private readonly Dictionary<string, DateTime> _lastRun = new();

    public EdgeRuntimeService(
        ILogger<EdgeRuntimeService> logger,
        IDeviceJobStore jobStore,
        ICollectorRegistry registry,
        MqttEdgeClient mqtt,
        IServiceProvider services)
    {
        _logger = logger;
        _jobStore = jobStore;
        _registry = registry;
        _mqtt = mqtt;
        _services = services;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        if (_jobStore is Config.JsonDeviceJobStore jsonStore)
            jsonStore.Load();

        foreach (var collector in _registry.GetAll())
        {
            await collector.InitializeAsync(new CollectorContext
            {
                Logger = _logger,
                Services = _services
            }, stoppingToken);
        }

        _mqtt.OnMessage(HandleMqttMessageAsync);
        await _mqtt.ConnectAsync(stoppingToken);

        while (!stoppingToken.IsCancellationRequested)
        {
            await RunScheduledJobsAsync(stoppingToken);
            await Task.Delay(TimeSpan.FromSeconds(1), stoppingToken);
        }
    }

    private async Task RunScheduledJobsAsync(CancellationToken cancellationToken)
    {
        foreach (var job in _jobStore.GetAll())
        {
            if (!job.Enabled || job.IntervalSeconds <= 0)
                continue;

            var last = _lastRun.GetValueOrDefault(job.JobId, DateTime.MinValue);
            if (DateTime.UtcNow - last < TimeSpan.FromSeconds(job.IntervalSeconds))
                continue;

            _lastRun[job.JobId] = DateTime.UtcNow;
            await ExecuteJobAsync(job, cancellationToken);
        }
    }

    private async Task ExecuteJobAsync(DeviceJobConfig job, CancellationToken cancellationToken)
    {
        var collector = _registry.Get(job.CollectorId);
        if (collector == null)
        {
            _logger.LogWarning("Collector not found: {CollectorId}", job.CollectorId);
            return;
        }

        var connectionJson = JsonSerializer.Serialize(job.Connection);
        var pointJson = JsonSerializer.Serialize(job.Points);

        var request = new CollectRequest
        {
            JobId = job.JobId,
            DeviceId = job.DeviceIdentification,
            SubDeviceIdentification = job.SubDeviceIdentification,
            CollectorId = job.CollectorId,
            ConnectionJson = connectionJson,
            PointConfigJson = pointJson
        };

        var result = await collector.CollectAsync(request, cancellationToken);
        if (!result.Success)
        {
            _logger.LogWarning("Collect failed job={JobId}: {Error}", job.JobId, result.ErrorMessage);
            return;
        }

        await _mqtt.PublishPropertyReportAsync(
            result.Variables,
            job.SubDeviceIdentification,
            job.SubProductIdentification,
            cancellationToken);

        _logger.LogInformation("Reported job={JobId} vars={Count}", job.JobId, result.Variables.Count);
    }

    private async Task HandleMqttMessageAsync(string topic, string payload)
    {
        try
        {
            if (topic.Contains("/config/downstream/push", StringComparison.OrdinalIgnoreCase))
            {
                var jobs = ConfigDownstreamParser.Parse(payload);
                if (jobs.Count > 0)
                {
                    _jobStore.ReplaceAll(jobs);
                    _lastRun.Clear();
                    _logger.LogInformation("Config pushed from cloud, jobs={Count}", jobs.Count);
                }
                return;
            }

            if (topic.Contains("/property/downstream/desired/set", StringComparison.OrdinalIgnoreCase))
            {
                var doc = JsonDocument.Parse(payload);
                var parameters = ExtractPropertySetParams(doc.RootElement);
                if (parameters.Count > 0)
                    await HandlePropertySetAsync(parameters);
                return;
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Handle MQTT message failed topic={Topic}", topic);
        }
    }

    private async Task HandlePropertySetAsync(Dictionary<string, object> values)
    {
        // 对首个可写采集任务执行属性下发
        var job = _jobStore.GetAll().FirstOrDefault(j =>
            j.CollectorId.StartsWith("modbus", StringComparison.OrdinalIgnoreCase)
            || j.CollectorId.StartsWith("opc", StringComparison.OrdinalIgnoreCase)
            || j.CollectorId.StartsWith("demo", StringComparison.OrdinalIgnoreCase));
        if (job == null)
        {
            await _mqtt.PublishDesiredSetAckAsync(false, "no writable job");
            return;
        }

        var collector = _registry.Get(job.CollectorId);
        if (collector == null)
        {
            await _mqtt.PublishDesiredSetAckAsync(false, "collector missing");
            return;
        }

        var write = new WriteRequest
        {
            JobId = job.JobId,
            DeviceId = job.DeviceIdentification,
            CollectorId = job.CollectorId,
            ConnectionJson = JsonSerializer.Serialize(job.Connection),
            PointConfigJson = JsonSerializer.Serialize(job.Points),
            Values = values
        };

        var result = await collector.WriteAsync(write);
        await _mqtt.PublishDesiredSetAckAsync(result.Success, result.ErrorMessage ?? "ok");
    }

    private static Dictionary<string, object> ExtractPropertySetParams(JsonElement root)
    {
        JsonElement parameters = root;
        if (root.TryGetProperty("params", out var paramsElement))
            parameters = paramsElement;

        if (parameters.ValueKind != JsonValueKind.Object)
            return new Dictionary<string, object>();

        if (parameters.TryGetProperty("input", out var input) && input.ValueKind == JsonValueKind.Object)
            return JsonSerializer.Deserialize<Dictionary<string, object>>(input.GetRawText()) ?? new();

        if (parameters.TryGetProperty("properties", out var properties) && properties.ValueKind == JsonValueKind.Object)
            return JsonSerializer.Deserialize<Dictionary<string, object>>(properties.GetRawText()) ?? new();

        var map = JsonSerializer.Deserialize<Dictionary<string, object>>(parameters.GetRawText()) ?? new();
        map.Remove("productIdentification");
        map.Remove("deviceIdentification");
        map.Remove("deviceId");
        map.Remove("subDeviceIdentification");
        map.Remove("input");
        map.Remove("properties");
        return map;
    }
}
