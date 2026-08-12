using System.Text;
using System.Text.Json;
using EasyAIoT.Edge.Mqtt.Messages;
using EasyAIoT.Edge.Mqtt.Options;
using EasyAIoT.Edge.Mqtt.Topics;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using MQTTnet;
using MQTTnet.Client;
using MQTTnet.Protocol;

namespace EasyAIoT.Edge.Mqtt.Client;

public sealed class MqttEdgeClient : IAsyncDisposable
{
    private readonly EdgeGatewayOptions _gateway;
    private readonly EdgeMqttOptions _mqtt;
    private readonly ILogger<MqttEdgeClient> _logger;
    private readonly JsonSerializerOptions _jsonOptions = new() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };
    private IMqttClient? _client;
    private Func<string, string, Task>? _messageHandler;

    public MqttEdgeClient(
        IOptions<EdgeGatewayOptions> gatewayOptions,
        IOptions<EdgeMqttOptions> mqttOptions,
        ILogger<MqttEdgeClient> logger)
    {
        _gateway = gatewayOptions.Value;
        _mqtt = mqttOptions.Value;
        _logger = logger;
    }

    public bool IsConnected => _client?.IsConnected == true;

    public void OnMessage(Func<string, string, Task> handler) => _messageHandler = handler;

    public async Task ConnectAsync(CancellationToken cancellationToken = default)
    {
        var factory = new MqttFactory();
        _client = factory.CreateMqttClient();

        _client.ApplicationMessageReceivedAsync += async args =>
        {
            var topic = args.ApplicationMessage.Topic;
            var payload = args.ApplicationMessage.PayloadSegment.Count > 0
                ? Encoding.UTF8.GetString(args.ApplicationMessage.PayloadSegment)
                : "";
            if (_messageHandler != null)
                await _messageHandler(topic, payload);
        };

        _client.DisconnectedAsync += async _ =>
        {
            _logger.LogWarning("MQTT disconnected, reconnecting in 3s...");
            await Task.Delay(3000, cancellationToken);
            try { await ConnectAsync(cancellationToken); } catch (Exception ex) { _logger.LogError(ex, "MQTT reconnect failed"); }
        };

        var clientId = _mqtt.ClientId ?? $"edge-{Guid.NewGuid():N}";
        var options = new MqttClientOptionsBuilder()
            .WithTcpServer(_mqtt.Host, _mqtt.Port)
            .WithClientId(clientId)
            .WithCleanSession()
            .WithTlsOptions(new MqttClientTlsOptions { UseTls = _mqtt.UseTls });

        if (!string.IsNullOrWhiteSpace(_mqtt.Username))
            options.WithCredentials(_mqtt.Username, _mqtt.Password);

        await _client.ConnectAsync(options.Build(), cancellationToken);
        await SubscribeDownstreamAsync(cancellationToken);
        _logger.LogInformation("MQTT connected to {Host}:{Port}", _mqtt.Host, _mqtt.Port);
    }

    private async Task SubscribeDownstreamAsync(CancellationToken cancellationToken)
    {
        var product = _gateway.ProductIdentification;
        var device = _gateway.DeviceIdentification;
        var topics = new[]
        {
            IotDeviceTopics.ConfigDownstreamPush(product, device),
            IotDeviceTopics.PropertyDownstreamDesiredSet(product, device),
            IotDeviceTopics.SubPropertyDownstreamDesiredSet(product, device)
        };

        foreach (var topic in topics)
        {
            await _client!.SubscribeAsync(new MqttTopicFilterBuilder()
                .WithTopic(topic)
                .WithQualityOfServiceLevel(MqttQualityOfServiceLevel.AtLeastOnce)
                .Build(), cancellationToken);
            _logger.LogInformation("MQTT subscribed: {Topic}", topic);
        }
    }

    public async Task PublishPropertyReportAsync(
        Dictionary<string, object> properties,
        string? subDeviceIdentification = null,
        string? subProductIdentification = null,
        CancellationToken cancellationToken = default)
    {
        var product = _gateway.ProductIdentification;
        var gateway = _gateway.DeviceIdentification;
        string topic;
        Dictionary<string, object> payloadParams;

        if (!string.IsNullOrWhiteSpace(subDeviceIdentification))
        {
            topic = IotDeviceTopics.SubPropertyUpstreamReport(product, gateway);
            payloadParams = new Dictionary<string, object>
            {
                ["productIdentification"] = subProductIdentification ?? subDeviceIdentification,
                ["deviceIdentification"] = subDeviceIdentification,
                ["properties"] = properties
            };
        }
        else
        {
            topic = IotDeviceTopics.PropertyUpstreamReport(product, gateway);
            payloadParams = properties;
        }

        var message = IotDeviceMessage.PropertyPost(payloadParams);
        await PublishJsonAsync(topic, message, cancellationToken);
    }

    public async Task PublishDesiredSetAckAsync(bool success, string message, CancellationToken cancellationToken = default)
    {
        var topic = IotDeviceTopics.PropertyUpstreamDesiredSetAck(
            _gateway.ProductIdentification, _gateway.DeviceIdentification);
        await PublishJsonAsync(topic, IotDeviceMessage.PropertySetAck(success, message), cancellationToken);
    }

    private async Task PublishJsonAsync(string topic, object payload, CancellationToken cancellationToken)
    {
        if (_client == null || !_client.IsConnected)
        {
            _logger.LogWarning("MQTT not connected, drop publish to {Topic}", topic);
            return;
        }

        var json = JsonSerializer.Serialize(payload, _jsonOptions);
        var appMessage = new MqttApplicationMessageBuilder()
            .WithTopic(topic)
            .WithPayload(json)
            .WithQualityOfServiceLevel(MqttQualityOfServiceLevel.AtLeastOnce)
            .Build();
        await _client.PublishAsync(appMessage, cancellationToken);
    }

    public async ValueTask DisposeAsync()
    {
        if (_client != null)
        {
            await _client.DisconnectAsync();
            _client.Dispose();
        }
    }
}
