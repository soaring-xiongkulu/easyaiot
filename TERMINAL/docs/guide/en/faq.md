# FAQ & Troubleshooting

## Installation Issues

### Antivirus flags the app / files get deleted

This software does not ship with a code-signing certificate, so unsigned executables may be falsely flagged by some antivirus engines (such as Windows Defender). This is a known issue with Go/Wails applications (see [wailsapp/wails#3308](https://github.com/wailsapp/wails/issues/3308)).

- Add an exclusion rule in your antivirus software to allow the app
- Download only from the official open-source channels: [GitHub](https://github.com/ys-ll/uniterm/releases) and [Gitee](https://gitee.com/ys-l/uniterm/releases)
- If in doubt, you can download the source code and build it yourself

## Connection Issues

### SSH connection failed — "Connection refused"

- Verify the SSH service is running on the target server
- Check that the IP address and port are correct
- Check whether the firewall allows the port

### SSH key authentication failed

- Verify the key file path and permissions are correct; if the private key is passphrase-protected, enter it in the Key Password field
- Use the one-click Use Default Key button in the key path field to auto-fill the standard local OpenSSH key
- You can also paste a PEM private key directly in the Key Text field, or use a [Keystore](/en/features/keystore) identity
- Ensure the server's `~/.ssh/authorized_keys` contains the corresponding public key
- Try password authentication to verify server reachability

### SSH keyboard-interactive authentication rejected

When the server rejects keyboard-interactive authentication outright, the error message shows the raw reason returned by the server — use it to diagnose the issue (e.g., account locked, PAM restrictions).

### Kerberos authentication failed

- On Windows, the current login session's credentials are used automatically; on Linux / macOS, run `kinit` first to obtain credentials
- When the target is an IP address, `host/<IP>@<REALM>` is requested, so the Kerberos Realm must be filled in; it can be left empty for domain-name targets
- Make sure the local clock is not skewed too far from the domain controller's clock

### The SSH Agent option does not appear

SSH Agent authentication is only available on Windows and macOS. On Windows, Pageant or the Windows OpenSSH Agent service must be running; on macOS, the system `SSH_AUTH_SOCK` is used.

### Serial connection unresponsive

- Confirm the serial port name is correct (COMx on Windows, /dev/ttyUSBx on Linux)
- Check that parameters such as the baud rate match the device
- Try enabling "Local Echo" to verify whether input is being sent

## Terminal Issues

### Backspace behaves oddly (deletes whole words, cannot delete characters)

The backspace key defaults to DEL (0x7F). If the connection was created in an older version with the backspace setting saved, manually change it back to DEL in the connection settings. Windows local terminals always use DEL.

### macOS input method drops, duplicates, or misfires keystrokes

Fast-typing character loss/duplication, IME Enter keystrokes accidentally triggering app shortcuts, and swallowed capital letters have been fixed — please upgrade to the latest version.

## Feature Issues

### AI Assistant not responding

- Verify the API address and key are configured correctly
- Check whether the network can reach the API endpoint; behind a system-wide proxy, AI requests support the Use System Proxy option
- Review the connection test result on the AI model configuration page

### Cloud Sync failed

- Verify the Git repository URL and access token are correct
- Ensure the repository is private
- Check whether the network can reach the Git service

## More Help

If your issue is not listed here, please reach out through the following channel:

- [GitHub Issues](https://github.com/ys-ll/uniterm/issues)
