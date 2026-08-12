using System.Text.Json;
using EasyAIoT.Edge.Abstractions.Config;
using EasyAIoT.Edge.Abstractions.Collectors;
using Microsoft.Extensions.Logging;
using Opc.Ua;
using Opc.Ua.Client;
using Opc.Ua.Configuration;

namespace EasyAIoT.Edge.Collectors.OpcUa;

/// <summary>
/// OPC UA 采集器。
/// </summary>
public sealed class OpcUaCollector : ICollector, IDisposable
{
    private readonly Dictionary<string, (Session Session, string Endpoint)> _sessions = new();
    private ILogger? _logger;

    public string CollectorId => "opc-ua";

    public IReadOnlyList<string> SupportedAgreementTypes => new[] { "opc-ua", "opcua" };

    public Task InitializeAsync(CollectorContext context, CancellationToken cancellationToken = default)
    {
        _logger = context.Logger;
        return Task.CompletedTask;
    }

    public async Task<CollectResult> CollectAsync(CollectRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            var connection = JsonSerializer.Deserialize<ConnectionConfig>(request.ConnectionJson)
                ?? new ConnectionConfig();
            var points = JsonSerializer.Deserialize<List<PointConfig>>(request.PointConfigJson) ?? new();

            if (string.IsNullOrWhiteSpace(connection.EndpointUrl))
                return CollectResult.Fail("OPC UA endpointUrl is required");

            var session = await GetOrCreateSessionAsync(connection, request.JobId);
            var variables = new Dictionary<string, object>();

            foreach (var point in points)
            {
                if (string.IsNullOrWhiteSpace(point.NodeId))
                {
                    variables[point.Key] = "";
                    continue;
                }

                var nodeId = NodeId.Parse(point.NodeId);
                var value = session.ReadValue(nodeId);
                variables[point.Key] = ConvertValue(value);
            }

            return CollectResult.Ok(variables);
        }
        catch (Exception ex)
        {
            _logger?.LogError(ex, "OPC UA collect failed job={JobId}", request.JobId);
            return CollectResult.Fail(ex.Message);
        }
    }

    public async Task<WriteResult> WriteAsync(Abstractions.Collectors.WriteRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            var connection = JsonSerializer.Deserialize<ConnectionConfig>(request.ConnectionJson)
                ?? new ConnectionConfig();
            var points = JsonSerializer.Deserialize<List<PointConfig>>(request.PointConfigJson) ?? new();

            if (string.IsNullOrWhiteSpace(connection.EndpointUrl))
                return WriteResult.Fail("OPC UA endpointUrl is required");

            var session = await GetOrCreateSessionAsync(connection, request.JobId);

            var nodesToWrite = new List<WriteValue>();
            foreach (var kv in request.Values)
            {
                var point = points.FirstOrDefault(p => p.Key == kv.Key);
                if (point == null || string.IsNullOrWhiteSpace(point.NodeId))
                    continue;

                nodesToWrite.Add(new WriteValue
                {
                    NodeId = NodeId.Parse(point.NodeId),
                    AttributeId = Attributes.Value,
                    Value = new DataValue(new Variant(kv.Value))
                });
            }

            if (nodesToWrite.Count == 0)
                return WriteResult.Fail("no writable node");

            var collection = new WriteValueCollection(nodesToWrite);
            session.Write(null, collection, out var results, out _);
            if (results != null)
            {
                foreach (var status in results)
                {
                    if (StatusCode.IsBad(status))
                        return WriteResult.Fail(StatusCodes.GetBrowseName(status.Code));
                }
            }

            return WriteResult.Ok();
        }
        catch (Exception ex)
        {
            return WriteResult.Fail(ex.Message);
        }
    }

    public Task StopAsync(CancellationToken cancellationToken = default)
    {
        foreach (var entry in _sessions.Values)
        {
            try
            {
                entry.Session.Close();
                entry.Session.Dispose();
            }
            catch { /* ignore */ }
        }
        _sessions.Clear();
        return Task.CompletedTask;
    }

    private async Task<Session> GetOrCreateSessionAsync(ConnectionConfig connection, string jobId)
    {
        if (_sessions.TryGetValue(jobId, out var cached) && cached.Session.Connected)
            return cached.Session;

        var endpointUrl = connection.EndpointUrl!;
        var application = new ApplicationInstance
        {
            ApplicationName = "EasyAIoT.Edge.OpcUa",
            ApplicationType = ApplicationType.Client,
            ApplicationConfiguration = await BuildApplicationConfigurationAsync()
        };

        var selectedEndpoint = CoreClientUtils.SelectEndpoint(endpointUrl, useSecurity: false);
        var endpointConfiguration = EndpointConfiguration.Create(application.ApplicationConfiguration);
        var endpoint = new ConfiguredEndpoint(null, selectedEndpoint, endpointConfiguration);

        var session = await Session.Create(
            application.ApplicationConfiguration,
            endpoint,
            updateBeforeConnect: false,
            checkDomain: false,
            sessionName: "EasyAIoT.Edge",
            sessionTimeout: 60_000,
            identity: BuildUserIdentity(connection),
            preferredLocales: null);

        _sessions[jobId] = (session, endpointUrl);
        return session;
    }

    private static async Task<ApplicationConfiguration> BuildApplicationConfigurationAsync()
    {
        var config = new ApplicationConfiguration
        {
            ApplicationName = "EasyAIoT.Edge.OpcUa",
            ApplicationUri = "urn:EasyAIoT:Edge:OpcUa",
            ApplicationType = ApplicationType.Client,
            SecurityConfiguration = new SecurityConfiguration
            {
                ApplicationCertificate = new CertificateIdentifier(),
                AutoAcceptUntrustedCertificates = true,
                RejectSHA1SignedCertificates = false
            },
            TransportQuotas = new TransportQuotas { OperationTimeout = 15_000 },
            ClientConfiguration = new ClientConfiguration { DefaultSessionTimeout = 60_000 }
        };
        await config.Validate(ApplicationType.Client);
        return config;
    }

    private static IUserIdentity BuildUserIdentity(ConnectionConfig connection)
    {
        if (!string.IsNullOrWhiteSpace(connection.Username))
            return new UserIdentity(connection.Username, connection.Password ?? "");
        return new UserIdentity();
    }

    private static object ConvertValue(DataValue dataValue)
    {
        if (dataValue?.Value == null)
            return "";
        if (dataValue.Value is float f)
            return Math.Round(f, 6);
        if (dataValue.Value is double d)
            return Math.Round(d, 6);
        return dataValue.Value;
    }

    public void Dispose() => StopAsync().GetAwaiter().GetResult();
}
