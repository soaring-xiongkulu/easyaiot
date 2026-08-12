using EasyAIoT.Edge.Abstractions.Collectors;
using Microsoft.Extensions.DependencyInjection;

namespace EasyAIoT.Edge.Collectors.OpcUa;

public static class OpcUaCollectorExtensions
{
    public static IServiceCollection AddOpcUaCollectors(this IServiceCollection services)
    {
        services.AddSingleton<OpcUaCollector>();
        services.AddSingleton<ICollector>(sp => sp.GetRequiredService<OpcUaCollector>());
        return services;
    }
}
