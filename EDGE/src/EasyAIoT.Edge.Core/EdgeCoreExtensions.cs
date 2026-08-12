using EasyAIoT.Edge.Abstractions.Collectors;
using EasyAIoT.Edge.Abstractions.Config;
using EasyAIoT.Edge.Core.Config;
using EasyAIoT.Edge.Core.Hosting;
using EasyAIoT.Edge.Core.Registry;
using EasyAIoT.Edge.Mqtt.Client;
using EasyAIoT.Edge.Mqtt.Options;
using Microsoft.Extensions.DependencyInjection;

namespace EasyAIoT.Edge.Core;

public static class EdgeCoreExtensions
{
    public static IServiceCollection AddEdgeCore(this IServiceCollection services, string deviceJobsFilePath)
    {
        services.AddSingleton<IDeviceJobStore>(_ => new JsonDeviceJobStore(deviceJobsFilePath));
        services.AddSingleton<ICollectorRegistry, CollectorRegistry>();
        services.AddSingleton<MqttEdgeClient>();
        services.Configure<EdgeGatewayOptions>(o => { }); // bound from Host configuration
        services.Configure<EdgeMqttOptions>(o => { });
        services.AddHostedService<EdgeRuntimeService>();
        return services;
    }
}
