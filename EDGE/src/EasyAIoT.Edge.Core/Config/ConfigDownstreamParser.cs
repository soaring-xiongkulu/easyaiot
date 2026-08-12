using System.Text.Json;
using EasyAIoT.Edge.Abstractions.Config;

namespace EasyAIoT.Edge.Core.Config;

/// <summary>
/// 解析 MQTT thing.config.push 及多种 params 形态。
/// </summary>
public static class ConfigDownstreamParser
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    public static List<DeviceJobConfig> Parse(string payload)
    {
        using var doc = JsonDocument.Parse(payload);
        var root = doc.RootElement;

        if (root.ValueKind == JsonValueKind.Array)
            return DeserializeJobs(root.GetRawText());

        if (root.TryGetProperty("params", out var parameters))
            return ParseParams(parameters);

        if (root.TryGetProperty("jobs", out var jobs))
            return DeserializeJobs(jobs.GetRawText());

        if (root.TryGetProperty("edgeJobs", out var edgeJobs))
            return ParseEdgeJobItems(edgeJobs);

        if (root.TryGetProperty("protocolConfig", out _))
            return new List<DeviceJobConfig> { EdgeConfigMapper.FromIndustrial(
                Guid.NewGuid().ToString("N"), "", null,
                JsonSerializer.Deserialize<IndustrialProtocolConfig>(root.GetRawText(), JsonOptions) ?? new()) };

        return new List<DeviceJobConfig>();
    }

    private static List<DeviceJobConfig> ParseParams(JsonElement parameters)
    {
        if (parameters.ValueKind == JsonValueKind.Array)
            return DeserializeJobs(parameters.GetRawText());

        if (parameters.TryGetProperty("jobs", out var jobs))
            return DeserializeJobs(jobs.GetRawText());

        if (parameters.TryGetProperty("edgeJobs", out var edgeJobs))
            return ParseEdgeJobItems(edgeJobs);

        if (parameters.TryGetProperty("protocolConfig", out var protocolConfig))
        {
            var protocol = JsonSerializer.Deserialize<IndustrialProtocolConfig>(protocolConfig.GetRawText(), JsonOptions)
                ?? new IndustrialProtocolConfig();
            var deviceId = parameters.TryGetProperty("deviceIdentification", out var d)
                ? d.GetString() ?? "" : "";
            var subId = parameters.TryGetProperty("subDeviceIdentification", out var s)
                ? s.GetString() : null;
            var jobId = parameters.TryGetProperty("jobId", out var j) ? j.GetString() ?? Guid.NewGuid().ToString("N") : Guid.NewGuid().ToString("N");
            return new List<DeviceJobConfig> { EdgeConfigMapper.FromIndustrial(jobId, deviceId, subId, protocol) };
        }

        return new List<DeviceJobConfig>();
    }

    private static List<DeviceJobConfig> ParseEdgeJobItems(JsonElement edgeJobs)
    {
        var items = JsonSerializer.Deserialize<List<EdgeJobPushItem>>(edgeJobs.GetRawText(), JsonOptions) ?? new();
        return items.Select(EdgeConfigMapper.FromPushItem).ToList();
    }

    private static List<DeviceJobConfig> DeserializeJobs(string json)
    {
        var direct = JsonSerializer.Deserialize<List<DeviceJobConfig>>(json, JsonOptions);
        if (direct != null && direct.Count > 0)
            return direct;

        var items = JsonSerializer.Deserialize<List<EdgeJobPushItem>>(json, JsonOptions);
        if (items != null && items.Count > 0)
            return items.Select(EdgeConfigMapper.FromPushItem).ToList();

        return new List<DeviceJobConfig>();
    }
}
