namespace EasyAIoT.Edge.Abstractions.Collectors;

public sealed class CollectResult
{
    public bool Success { get; init; }

    public Dictionary<string, object> Variables { get; init; } = new();

    public string? RawHex { get; init; }

    public string? ErrorMessage { get; init; }

    public static CollectResult Ok(Dictionary<string, object> variables, string? rawHex = null) =>
        new() { Success = true, Variables = variables, RawHex = rawHex };

    public static CollectResult Fail(string message) =>
        new() { Success = false, ErrorMessage = message };
}
