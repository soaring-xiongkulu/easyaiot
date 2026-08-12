using System.IO.Ports;
using System.Threading.Channels;

namespace EasyAIoT.Edge.Hardware.Serial;

/// <summary>
/// RS485 串口单消费者队列。
/// </summary>
public sealed class SerialPortChannel
{
    private readonly Channel<SerialWorkItem> _channel =
        Channel.CreateUnbounded<SerialWorkItem>(new UnboundedChannelOptions { SingleReader = true });

    private readonly SerialPortHelper _helper = new();
    private readonly CancellationTokenSource _cts = new();
    private Task? _worker;

    public void Start()
    {
        _worker ??= Task.Run(ConsumeLoopAsync);
    }

    public async Task<string> EnqueueAsync(string portName, int baudRate, string hexFrame, CancellationToken cancellationToken = default)
    {
        var tcs = new TaskCompletionSource<string>(TaskCreationOptions.RunContinuationsAsynchronously);
        var item = new SerialWorkItem(portName, baudRate, hexFrame, tcs);
        await _channel.Writer.WriteAsync(item, cancellationToken);
        return await tcs.Task.WaitAsync(cancellationToken);
    }

    private async Task ConsumeLoopAsync()
    {
        await foreach (var item in _channel.Reader.ReadAllAsync(_cts.Token))
        {
            try
            {
                var result = _helper.ExchangeHex(portName: item.PortName, baudRate: item.BaudRate, sendHex: item.HexFrame);
                item.Completion.SetResult(result);
            }
            catch (Exception ex)
            {
                item.Completion.SetException(ex);
            }
        }
    }

    public async ValueTask DisposeAsync()
    {
        _channel.Writer.TryComplete();
        _cts.Cancel();
        if (_worker != null)
        {
            try { await _worker; } catch (OperationCanceledException) { }
        }
        _helper.Dispose();
        _cts.Dispose();
    }

    private sealed record SerialWorkItem(
        string PortName,
        int BaudRate,
        string HexFrame,
        TaskCompletionSource<string> Completion);
}
