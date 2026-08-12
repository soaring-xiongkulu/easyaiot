using EasyAIoT.Edge.Abstractions.Collectors;

namespace EasyAIoT.Edge.Core.Registry;

public sealed class CollectorRegistry : ICollectorRegistry
{
    private readonly Dictionary<string, ICollector> _collectors = new(StringComparer.OrdinalIgnoreCase);

    public void Register(ICollector collector) => _collectors[collector.CollectorId] = collector;

    public ICollector? Get(string collectorId) => _collectors.TryGetValue(collectorId, out var c) ? c : null;

    public IReadOnlyList<ICollector> GetAll() => _collectors.Values.ToList();
}
