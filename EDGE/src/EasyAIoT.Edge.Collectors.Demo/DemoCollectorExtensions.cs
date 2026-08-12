using EasyAIoT.Edge.Abstractions.Collectors;
using Microsoft.Extensions.DependencyInjection;

namespace EasyAIoT.Edge.Collectors.Demo;

public static class DemoCollectorExtensions
{
    public static IServiceCollection AddDemoCollectors(this IServiceCollection services)
    {
        services.AddSingleton<DemoSimulatorCollector>();
        services.AddSingleton<ICollector>(sp => sp.GetRequiredService<DemoSimulatorCollector>());
        return services;
    }
}
