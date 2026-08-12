using System.IO.Ports;

namespace EasyAIoT.Edge.Hardware.Serial;

/// <summary>
/// 串口 hex 收发。
/// </summary>
public sealed class SerialPortHelper : IDisposable
{
    private readonly object _lock = new();
    private SerialPort? _serialPort;
    private string _portName = "";
    private int _baudRate;

    public string ExchangeHex(string portName, int baudRate, string sendHex)
    {
        lock (_lock)
        {
            OpenIfNeeded(portName, baudRate);
            var sendBytes = HexConverter.HexToBytes(sendHex);
            _serialPort!.Write(sendBytes, 0, sendBytes.Length);

            int stableCount = 0;
            int lastBytes = 0;
            for (int i = 0; i < 25; i++)
            {
                int current = _serialPort.BytesToRead;
                if (current > 0 && current == lastBytes)
                {
                    stableCount++;
                    if (stableCount >= 2)
                        break;
                }
                else
                {
                    stableCount = 0;
                }

                lastBytes = current;
                Thread.Sleep(30);
            }

            if (_serialPort.BytesToRead == 0)
                return "";

            var buffer = new byte[_serialPort.BytesToRead];
            _serialPort.Read(buffer, 0, buffer.Length);
            return HexConverter.BytesToHex(buffer);
        }
    }

    private void OpenIfNeeded(string portName, int baudRate)
    {
        if (_serialPort != null && _serialPort.IsOpen && _portName == portName && _baudRate == baudRate)
            return;

        if (_serialPort != null)
        {
            if (_serialPort.IsOpen)
                _serialPort.Close();
            _serialPort.Dispose();
        }

        _serialPort = new SerialPort(portName, baudRate, Parity.None, 8, StopBits.One)
        {
            ReadBufferSize = 4096,
            WriteBufferSize = 2048
        };
        _serialPort.Open();
        _portName = portName;
        _baudRate = baudRate;
    }

    public void Dispose()
    {
        lock (_lock)
        {
            if (_serialPort != null)
            {
                if (_serialPort.IsOpen)
                    _serialPort.Close();
                _serialPort.Dispose();
                _serialPort = null;
            }
        }
    }
}
