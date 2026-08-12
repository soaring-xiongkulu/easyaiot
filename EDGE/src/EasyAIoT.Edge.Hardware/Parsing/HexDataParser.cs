using EasyAIoT.Edge.Abstractions.Config;
using EasyAIoT.Edge.Hardware.Serial;

namespace EasyAIoT.Edge.Hardware.Parsing;

/// <summary>
/// 配置驱动的 hex 解析，将 GatewayServer 硬编码解析下沉为通用规则。
/// </summary>
public static class HexDataParser
{
    public static object Parse(byte[] data, ParseRule rule)
    {
        if (rule.Offset + rule.Length > data.Length)
            throw new InvalidOperationException($"Parse offset out of range: offset={rule.Offset}, length={rule.Length}, dataLen={data.Length}");

        var slice = data.AsSpan(rule.Offset, rule.Length);
        double value;

        switch (rule.Type.ToLowerInvariant())
        {
            case "hex":
                return HexConverter.BytesToHex(slice.ToArray());
            case "int16":
                value = BitConverter.ToInt16(NormalizeEndian(slice, 2));
                break;
            case "uint16":
                value = BitConverter.ToUInt16(NormalizeEndian(slice, 2));
                break;
            case "int32":
                value = BitConverter.ToInt32(NormalizeEndian(slice, 4));
                break;
            case "float":
                value = BitConverter.ToSingle(NormalizeEndian(slice, 4));
                break;
            default:
                value = BitConverter.ToUInt16(NormalizeEndian(slice, 2));
                break;
        }

        if (rule.SignedComplement && rule.Type.Equals("int16", StringComparison.OrdinalIgnoreCase) && value > 32767)
            value -= 65536;

        value = value * rule.Scale + rule.OffsetValue;
        return Math.Round(value, 6);
    }

    private static byte[] NormalizeEndian(ReadOnlySpan<byte> slice, int width)
    {
        var bytes = slice.ToArray();
        if (bytes.Length < width)
            throw new InvalidOperationException("Insufficient bytes for type width");
        if (bytes.Length > width)
            bytes = bytes[..width];
        return bytes;
    }
}
