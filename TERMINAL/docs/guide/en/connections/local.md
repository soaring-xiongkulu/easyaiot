# Local

Open a terminal directly on the local machine, open a WSL distribution, or connect to serial devices without a network.

## Local Shell

### Connection Parameters

| Parameter | Description |
|------|------|
| Shell Type | Select which local shell to open |
| Character Encoding | Terminal charset, default UTF-8. Also supports GBK, GB2312, Big5, Shift-JIS, etc. |
| Startup Script | Commands or scripts automatically executed after the terminal starts (optional) |
| Start Recording Log on Connect | Automatically start recording the session log when the connection is established |

Supported shell types (detected automatically depending on the operating system):

**Windows:**
- PowerShell
- CMD
- Command Prompt (Clink)
- Command Prompt (Admin) / PowerShell (Admin) -- elevated through UAC and embedded as a regular tab
- Git Bash
- Cygwin / MSYS2
- Nushell

**macOS / Linux:**
- bash
- zsh
- Other installed shells

## WSL

Open WSL Linux distributions installed on Windows (such as Ubuntu or Debian). Each distribution is listed as a separate shell.

**WSL file management:** The Files sidebar supports browsing and managing files in WSL distributions directly, without installing anything inside the distribution. See [Sidebar](/en/features/sidebar) for details.

## Serial

Connect to serial devices such as router consoles, embedded development boards, industrial equipment, etc.

### Connection Parameters

| Parameter | Description |
|------|------|
| Port | Serial port name (COMx on Windows, /dev/ttyUSBx on Linux) |
| Baud Rate | Transmission rate, commonly 9600 or 115200 |
| Data Bits | Data bits per frame, commonly 8 |
| Stop Bits | Stop bits, commonly 1 |
| Parity | Error detection, options: None, Even, Odd, Mark, Space |
| Character Encoding | Terminal charset, default UTF-8. Also supports GBK, GB2312, Big5, Shift-JIS, etc. |
| Backspace Key | Byte sequence sent by the terminal backspace key, default ASCII Delete (0x7F). Also supports ASCII Backspace (0x08) and VT220 Delete (ESC[3~) |
| Local Echo | Whether to display input locally; enable as needed |
| Newline Mode | CR (default) or CR+LF |
| Start Recording Log on Connect | Automatically start recording the session log when the connection is established |


::: tip Related
- [Remote Terminal](/en/connections/remote-terminal) -- SSH/Telnet/Mosh remote connections
- [Sidebar](/en/features/sidebar) -- Quick launch entry for local shells
:::
