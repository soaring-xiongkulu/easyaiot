using System.Text.Json;
using EasyAIoT.Edge.Abstractions.Config;
using EasyAIoT.Edge.Abstractions.Collectors;
using EasyAIoT.Edge.Hardware.Modbus;
using EasyAIoT.Edge.Hardware.Serial;
using Microsoft.Extensions.Logging;

namespace EasyAIoT.Edge.Collectors.Modbus;

/// <summary>
/// Modbus TCP 采集器。
/// </summary>
public sealed class ModbusTcpCollector : ICollector
{
    private ILogger? _logger;

    public string CollectorId => "modbus-tcp";

    public IReadOnlyList<string> SupportedAgreementTypes => new[] { "tcp", "modbus-tcp" };

    public Task InitializeAsync(CollectorContext context, CancellationToken cancellationToken = default)
    {
        _logger = context.Logger;
        return Task.CompletedTask;
    }

    public Task<CollectResult> CollectAsync(CollectRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            var connection = JsonSerializer.Deserialize<ConnectionConfig>(request.ConnectionJson)
                ?? new ConnectionConfig();
            var points = JsonSerializer.Deserialize<List<PointConfig>>(request.PointConfigJson) ?? new();

            if (string.IsNullOrWhiteSpace(connection.Host))
                return Task.FromResult(CollectResult.Fail("Modbus TCP host is required"));

            var variables = new Dictionary<string, object>();
            var rawParts = new List<string>();

            foreach (var point in points)
            {
                var pdu = ModbusCollectHelper.BuildPdu(connection.SlaveId, point);
                var response = ModbusTcpClient.Exchange(connection.Host, connection.Port, pdu);
                if (response.Length == 0)
                {
                    variables[point.Key] = "";
                    continue;
                }

                rawParts.Add(HexConverter.BytesToHex(response));
                foreach (var kv in ModbusCollectHelper.ParsePoints(new List<PointConfig> { point }, response))
                    variables[kv.Key] = kv.Value;
            }

            return Task.FromResult(CollectResult.Ok(variables, string.Join("|", rawParts)));
        }
        catch (Exception ex)
        {
            _logger?.LogError(ex, "Modbus TCP collect failed job={JobId}", request.JobId);
            return Task.FromResult(CollectResult.Fail(ex.Message));
        }
    }

    public Task<WriteResult> WriteAsync(WriteRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            var connection = JsonSerializer.Deserialize<ConnectionConfig>(request.ConnectionJson)
                ?? new ConnectionConfig();
            var points = JsonSerializer.Deserialize<List<PointConfig>>(request.PointConfigJson) ?? new();

            if (string.IsNullOrWhiteSpace(connection.Host))
                return Task.FromResult(WriteResult.Fail("Modbus TCP host is required"));

            foreach (var kv in request.Values)
            {
                var point = points.FirstOrDefault(p => p.Key == kv.Key);
                if (point == null)
                    continue;

                var value = Convert.ToUInt16(kv.Value);
                var pdu = new byte[]
                {
                    (byte)connection.SlaveId,
                    0x06,
                    (byte)(point.Address >> 8),
                    (byte)(point.Address & 0xFF),
                    (byte)(value >> 8),
                    (byte)(value & 0xFF)
                };
                ModbusTcpClient.Exchange(connection.Host, connection.Port, pdu);
            }

            return Task.FromResult(WriteResult.Ok());
        }
        catch (Exception ex)
        {
            return Task.FromResult(WriteResult.Fail(ex.Message));
        }
    }

    public Task StopAsync(CancellationToken cancellationToken = default) => Task.CompletedTask;
}
