using System.Text.Json;
using EasyAIoT.Edge.Abstractions.Config;
using EasyAIoT.Edge.Abstractions.Collectors;
using EasyAIoT.Edge.Hardware.Modbus;
using EasyAIoT.Edge.Hardware.Parsing;
using EasyAIoT.Edge.Hardware.Serial;
using Microsoft.Extensions.Logging;

namespace EasyAIoT.Edge.Collectors.Modbus;

/// <summary>
/// Modbus RTU 采集器（RS485/串口）。
/// </summary>
public sealed class ModbusRtuCollector : ICollector
{
    private readonly SerialPortChannel _channel = new();
    private ILogger? _logger;

    public string CollectorId => "modbus-rtu";

    public IReadOnlyList<string> SupportedAgreementTypes => new[] { "rs485", "serial" };

    public Task InitializeAsync(CollectorContext context, CancellationToken cancellationToken = default)
    {
        _logger = context.Logger;
        _channel.Start();
        return Task.CompletedTask;
    }

    public async Task<CollectResult> CollectAsync(CollectRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            var connection = JsonSerializer.Deserialize<ConnectionConfig>(request.ConnectionJson)
                ?? new ConnectionConfig();
            var points = JsonSerializer.Deserialize<List<PointConfig>>(request.PointConfigJson) ?? new();

            var variables = new Dictionary<string, object>();
            var rawParts = new List<string>();

            foreach (var point in points)
            {
                var frameHex = BuildFrameHex(connection.SlaveId, point);
                var responseHex = await _channel.EnqueueAsync(
                    connection.PortName, connection.BaudRate, frameHex, cancellationToken);

                if (string.IsNullOrWhiteSpace(responseHex))
                {
                    variables[point.Key] = "";
                    continue;
                }

                rawParts.Add(responseHex);
                var bytes = HexConverter.HexToBytes(responseHex);
                var value = HexDataParser.Parse(bytes, point.Parse);
                variables[point.Key] = value;
            }

            return CollectResult.Ok(variables, string.Join("|", rawParts));
        }
        catch (Exception ex)
        {
            _logger?.LogError(ex, "Modbus RTU collect failed job={JobId}", request.JobId);
            return CollectResult.Fail(ex.Message);
        }
    }

    public Task<WriteResult> WriteAsync(WriteRequest request, CancellationToken cancellationToken = default)
    {
        // 首版：写单寄存器 function 6
        try
        {
            var connection = JsonSerializer.Deserialize<ConnectionConfig>(request.ConnectionJson)
                ?? new ConnectionConfig();
            var points = JsonSerializer.Deserialize<List<PointConfig>>(request.PointConfigJson) ?? new();

            foreach (var kv in request.Values)
            {
                var point = points.FirstOrDefault(p => p.Key == kv.Key);
                if (point == null)
                    continue;

                var value = Convert.ToUInt16(kv.Value);
                var frame = new byte[]
                {
                    (byte)connection.SlaveId,
                    0x06,
                    (byte)(point.Address >> 8),
                    (byte)(point.Address & 0xFF),
                    (byte)(value >> 8),
                    (byte)(value & 0xFF)
                };
                var withCrc = ModbusCrc16.AppendCrc(frame);
                var hex = HexConverter.BytesToHex(withCrc);
                _ = _channel.EnqueueAsync(connection.PortName, connection.BaudRate, hex, cancellationToken);
            }

            return Task.FromResult(WriteResult.Ok());
        }
        catch (Exception ex)
        {
            return Task.FromResult(WriteResult.Fail(ex.Message));
        }
    }

    public Task StopAsync(CancellationToken cancellationToken = default) =>
        _channel.DisposeAsync().AsTask();

    private static string BuildFrameHex(int slaveId, PointConfig point)
    {
        if (!string.IsNullOrWhiteSpace(point.HexFrame))
            return point.HexFrame.Replace(" ", "");

        var frame = ModbusCrc16.BuildReadFrame(slaveId, point.Function, point.Address, point.Length);
        return HexConverter.BytesToHex(frame);
    }
}
