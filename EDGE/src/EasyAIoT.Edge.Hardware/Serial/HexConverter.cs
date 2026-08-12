namespace EasyAIoT.Edge.Hardware.Serial;

public static class HexConverter
{
    public static byte[] HexToBytes(string hex)
    {
        var normalized = hex.Replace(" ", "").Replace("-", "");
        if (normalized.Length % 2 != 0)
            throw new ArgumentException("Invalid hex length", nameof(hex));

        var bytes = new byte[normalized.Length / 2];
        for (int i = 0; i < bytes.Length; i++)
            bytes[i] = Convert.ToByte(normalized.Substring(i * 2, 2), 16);
        return bytes;
    }

    public static string BytesToHex(byte[] bytes)
    {
        return BitConverter.ToString(bytes).Replace("-", "");
    }

    public static string BytesToHexSpaced(byte[] bytes)
    {
        return BitConverter.ToString(bytes).Replace("-", " ");
    }
}
