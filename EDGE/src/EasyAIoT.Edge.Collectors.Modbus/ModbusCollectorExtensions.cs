using EasyAIoT.Edge.Abstractions.Collectors;
using EasyAIoT.Edge.Collectors.Modbus;
using Microsoft.Extensions.DependencyInjection;

namespace EasyAIoT.Edge.Collectors.Modbus;

public static class ModbusCollectorExtensions
{
    public static IServiceCollection AddModbusCollectors(this IServiceCollection services)
    {
        services.AddSingleton<ModbusRtuCollector>();
        services.AddSingleton<ModbusTcpCollector>();
        services.AddSingleton<ICollector>(sp => sp.GetRequiredService<ModbusRtuCollector>());
        services.AddSingleton<ICollector>(sp => sp.GetRequiredService<ModbusTcpCollector>());
        return services;
    }
}
