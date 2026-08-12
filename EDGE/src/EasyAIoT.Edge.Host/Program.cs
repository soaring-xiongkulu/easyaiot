using EasyAIoT.Edge.Abstractions.Collectors;
using EasyAIoT.Edge.Collectors.Demo;
using EasyAIoT.Edge.Collectors.Modbus;
using EasyAIoT.Edge.Collectors.OpcUa;
using EasyAIoT.Edge.Core;
using EasyAIoT.Edge.Mqtt.Options;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var contentRoot = AppContext.BaseDirectory;
var jobsFile = Path.Combine(contentRoot, "data", "device-jobs.json");

var builder = Host.CreateApplicationBuilder(args);

builder.Services.Configure<EdgeGatewayOptions>(
    builder.Configuration.GetSection(EdgeGatewayOptions.SectionName));
builder.Services.Configure<EdgeMqttOptions>(
    builder.Configuration.GetSection(EdgeMqttOptions.SectionName));

builder.Services.AddEdgeCore(jobsFile);
builder.Services.AddModbusCollectors();
builder.Services.AddOpcUaCollectors();
builder.Services.AddDemoCollectors();

var host = builder.Build();

var registry = host.Services.GetRequiredService<ICollectorRegistry>();
foreach (var collector in host.Services.GetServices<ICollector>())
    registry.Register(collector);

Console.WriteLine("EasyAIoT EDGE collector starting...");
Console.WriteLine("Device jobs file: {0}", jobsFile);

await host.RunAsync();
