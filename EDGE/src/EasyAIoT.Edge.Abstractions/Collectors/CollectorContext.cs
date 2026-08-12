using Microsoft.Extensions.Logging;

namespace EasyAIoT.Edge.Abstractions.Collectors;

public sealed class CollectorContext
{
    public required ILogger Logger { get; init; }

    public required IServiceProvider Services { get; init; }
}
