namespace EasyAIoT.Edge.Hardware.Modbus;

/// <summary>
/// Modbus CRC16。
/// </summary>
public static class ModbusCrc16
{
    public static ushort Compute(byte[] data)
    {
        ushort crc = 0xFFFF;
        foreach (var b in data)
        {
            crc ^= b;
            for (int i = 0; i < 8; i++)
            {
                if ((crc & 0x0001) != 0)
                    crc = (ushort)((crc >> 1) ^ 0xA001);
                else
                    crc >>= 1;
            }
        }
        return crc;
    }

    public static byte[] AppendCrc(byte[] frameWithoutCrc)
    {
        var crc = Compute(frameWithoutCrc);
        var result = new byte[frameWithoutCrc.Length + 2];
        Array.Copy(frameWithoutCrc, result, frameWithoutCrc.Length);
        result[^2] = (byte)(crc & 0xFF);
        result[^1] = (byte)(crc >> 8);
        return result;
    }

    public static byte[] BuildReadFrame(int slaveId, int function, int address, int quantity)
    {
        var frame = new byte[]
        {
            (byte)slaveId,
            (byte)function,
            (byte)(address >> 8),
            (byte)(address & 0xFF),
            (byte)(quantity >> 8),
            (byte)(quantity & 0xFF)
        };
        return AppendCrc(frame);
    }
}
