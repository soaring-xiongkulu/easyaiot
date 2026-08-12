namespace EasyAIoT.Edge.Abstractions.Config;

public sealed class ParseRule
{
    /// <summary>响应字节偏移（从 0 起）。</summary>
    public int Offset { get; set; }

    public int Length { get; set; } = 2;

    /// <summary>int16 | uint16 | int32 | float | hex。</summary>
    public string Type { get; set; } = "uint16";

    public double Scale { get; set; } = 1.0;

    public double OffsetValue { get; set; } = 0.0;

    /// <summary>是否按补码解析有符号数。</summary>
    public bool SignedComplement { get; set; } = false;
}
