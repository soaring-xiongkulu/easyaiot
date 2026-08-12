using System.Net.Sockets;

namespace EasyAIoT.Edge.Hardware.Modbus;

public static class ModbusTcpClient
{
    public static byte[] Exchange(string host, int port, byte[] pdu, int timeoutMs = 5000)
    {
        using var client = new TcpClient();
        client.Connect(host, port);
        using var stream = client.GetStream();
        stream.ReadTimeout = timeoutMs;
        stream.WriteTimeout = timeoutMs;

        ushort transactionId = (ushort)Random.Shared.Next(1, ushort.MaxValue);
        var frame = BuildMbapFrame(transactionId, pdu);
        stream.Write(frame, 0, frame.Length);

        var header = ReadExact(stream, 7, timeoutMs);
        int length = (header[4] << 8) | header[5];
        if (length < 1)
            return Array.Empty<byte>();

        var payload = ReadExact(stream, length, timeoutMs);
        return payload;
    }

    private static byte[] BuildMbapFrame(ushort transactionId, byte[] pdu)
    {
        var frame = new byte[7 + pdu.Length];
        frame[0] = (byte)(transactionId >> 8);
        frame[1] = (byte)(transactionId & 0xFF);
        frame[2] = 0;
        frame[3] = 0;
        frame[4] = (byte)((pdu.Length >> 8) & 0xFF);
        frame[5] = (byte)(pdu.Length & 0xFF);
        frame[6] = 0;
        Array.Copy(pdu, 0, frame, 7, pdu.Length);
        return frame;
    }

    private static byte[] ReadExact(NetworkStream stream, int length, int timeoutMs)
    {
        var buffer = new byte[length];
        int offset = 0;
        var deadline = Environment.TickCount64 + timeoutMs;
        while (offset < length)
        {
            if (Environment.TickCount64 > deadline)
                throw new TimeoutException("Modbus TCP read timeout");
            if (stream.DataAvailable)
            {
                int read = stream.Read(buffer, offset, length - offset);
                if (read == 0)
                    throw new IOException("Modbus TCP connection closed");
                offset += read;
            }
            else
            {
                Thread.Sleep(10);
            }
        }
        return buffer;
    }
}
