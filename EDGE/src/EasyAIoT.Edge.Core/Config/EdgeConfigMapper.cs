using EasyAIoT.Edge.Abstractions.Config;

namespace EasyAIoT.Edge.Core.Config;

public static class EdgeConfigMapper
{
    public static DeviceJobConfig FromPushItem(EdgeJobPushItem item)
    {
        var protocol = item.ProtocolConfig ?? new IndustrialProtocolConfig();
        var collectorId = item.CollectorId ?? InferCollectorId(protocol.Type);

        var job = new DeviceJobConfig
        {
            JobId = string.IsNullOrWhiteSpace(item.JobId) ? Guid.NewGuid().ToString("N") : item.JobId,
            DeviceIdentification = item.DeviceIdentification ?? "",
            SubDeviceIdentification = item.SubDeviceIdentification,
            SubProductIdentification = item.SubProductIdentification,
            CollectorId = collectorId,
            AgreementType = item.AgreementType ?? InferAgreementType(collectorId),
            Enabled = item.Enabled ?? protocol.Enabled ?? true,
            IntervalSeconds = item.IntervalSeconds ?? MsToSeconds(protocol.PollIntervalMs),
            Connection = MapConnection(protocol),
            Points = MapPoints(protocol.Points)
        };
        return job;
    }

    public static DeviceJobConfig FromIndustrial(string jobId, string deviceId, string? subDeviceId, IndustrialProtocolConfig protocol)
    {
        var collectorId = InferCollectorId(protocol.Type);
        return new DeviceJobConfig
        {
            JobId = jobId,
            DeviceIdentification = deviceId,
            SubDeviceIdentification = subDeviceId,
            CollectorId = collectorId,
            AgreementType = InferAgreementType(collectorId),
            Enabled = protocol.Enabled ?? true,
            IntervalSeconds = MsToSeconds(protocol.PollIntervalMs),
            Connection = MapConnection(protocol),
            Points = MapPoints(protocol.Points)
        };
    }

    private static ConnectionConfig MapConnection(IndustrialProtocolConfig protocol)
    {
        return new ConnectionConfig
        {
            PortName = protocol.SerialPort ?? "/dev/ttyS3",
            BaudRate = protocol.BaudRate ?? 9600,
            Host = protocol.Host,
            Port = protocol.Port ?? 502,
            SlaveId = protocol.UnitId ?? 1,
            EndpointUrl = protocol.EndpointUrl,
            Username = protocol.Username,
            Password = protocol.Password
        };
    }

    private static List<PointConfig> MapPoints(List<IndustrialPointConfig> points)
    {
        var result = new List<PointConfig>();
        foreach (var p in points)
        {
            var key = p.ResolvedPropertyCode();
            if (string.IsNullOrWhiteSpace(key))
                continue;

            result.Add(new PointConfig
            {
                Key = key,
                Name = key,
                Function = MapModbusFunction(p.Function),
                Address = p.Address ?? 0,
                Length = p.Quantity ?? 1,
                NodeId = p.NodeId,
                Parse = new ParseRule
                {
                    Offset = 3,
                    Length = MapParseLength(p.DataType),
                    Type = MapDataType(p.DataType),
                    Scale = p.Scale ?? 1.0,
                    OffsetValue = p.Offset ?? 0.0
                }
            });
        }
        return result;
    }

    private static int MapModbusFunction(string? function)
    {
        if (string.IsNullOrWhiteSpace(function))
            return 3;
        switch (function.ToUpperInvariant())
        {
            case "COIL": return 1;
            case "DISCRETE_INPUT": return 2;
            case "INPUT_REGISTER": return 4;
            case "HOLDING_REGISTER": return 3;
            default:
                if (int.TryParse(function, out var n))
                    return n;
                return 3;
        }
    }

    private static string MapDataType(string? dataType)
    {
        if (string.IsNullOrWhiteSpace(dataType))
            return "uint16";
        switch (dataType.ToUpperInvariant())
        {
            case "INT16": return "int16";
            case "UINT16": return "uint16";
            case "INT32": return "int32";
            case "FLOAT": return "float";
            default: return "uint16";
        }
    }

    private static int MapParseLength(string? dataType)
    {
        if (string.IsNullOrWhiteSpace(dataType))
            return 2;
        switch (dataType.ToUpperInvariant())
        {
            case "INT32": return 4;
            case "FLOAT": return 4;
            default: return 2;
        }
    }

    private static string InferCollectorId(string? type)
    {
        if (string.IsNullOrWhiteSpace(type))
            return "modbus-rtu";
        switch (type.ToLowerInvariant())
        {
            case "modbus-tcp": return "modbus-tcp";
            case "modbus-rtu": return "modbus-rtu";
            case "opc-ua": return "opc-ua";
            case "opcua": return "opc-ua";
            default: return type.ToLowerInvariant();
        }
    }

    private static string InferAgreementType(string collectorId)
    {
        switch (collectorId.ToLowerInvariant())
        {
            case "modbus-tcp": return "tcp";
            case "opc-ua": return "opc-ua";
            default: return "rs485";
        }
    }

    private static int MsToSeconds(long? pollIntervalMs)
    {
        if (pollIntervalMs == null || pollIntervalMs <= 0)
            return 30;
        return (int)Math.Max(1L, pollIntervalMs.Value / 1000);
    }
}
