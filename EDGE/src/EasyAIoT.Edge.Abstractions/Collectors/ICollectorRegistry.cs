namespace EasyAIoT.Edge.Abstractions.Collectors;

public interface ICollectorRegistry
{
    void Register(ICollector collector);

    ICollector? Get(string collectorId);

    IReadOnlyList<ICollector> GetAll();
}
