using EasyAIoT.Edge.Abstractions.Config;
using EasyAIoT.Edge.Hardware.Modbus;
using EasyAIoT.Edge.Hardware.Parsing;
using EasyAIoT.Edge.Hardware.Serial;

namespace EasyAIoT.Edge.Collectors.Modbus;

internal static class ModbusCollectHelper
{
    public static string BuildFrameHex(int slaveId, PointConfig point)
    {
        if (!string.IsNullOrWhiteSpace(point.HexFrame))
            return point.HexFrame.Replace(" ", "");

        var frame = ModbusCrc16.BuildReadFrame(slaveId, point.Function, point.Address, point.Length);
        return HexConverter.BytesToHex(frame);
    }

    public static byte[] BuildPdu(int slaveId, PointConfig point)
    {
        return new byte[]
        {
            (byte)slaveId,
            (byte)point.Function,
            (byte)(point.Address >> 8),
            (byte)(point.Address & 0xFF),
            (byte)(point.Length >> 8),
            (byte)(point.Length & 0xFF)
        };
    }

    public static Dictionary<string, object> ParsePoints(List<PointConfig> points, byte[] responseBytes)
    {
        var variables = new Dictionary<string, object>();
        foreach (var point in points)
        {
            try
            {
                var value = HexDataParser.Parse(responseBytes, point.Parse);
                variables[point.Key] = value;
            }
            catch
            {
                variables[point.Key] = "";
            }
        }
        return variables;
    }
}
