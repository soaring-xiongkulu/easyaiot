namespace EasyAIoT.Edge.Abstractions.Collectors;

public sealed class WriteRequest
{
    public required string JobId { get; init; }

    public required string DeviceId { get; init; }

    public required string CollectorId { get; init; }

    public required string ConnectionJson { get; init; }

    public required string PointConfigJson { get; init; }

    public required Dictionary<string, object> Values { get; init; }
}

public sealed class WriteResult
{
    public bool Success { get; init; }

    public string? ErrorMessage { get; init; }

    public static WriteResult Ok() => new() { Success = true };

    public static WriteResult Fail(string message) =>
        new() { Success = false, ErrorMessage = message };
}
