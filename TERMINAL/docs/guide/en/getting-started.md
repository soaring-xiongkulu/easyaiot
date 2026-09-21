# Installation and First Connection

This guide will help you download, install 终端, and establish your first connection.


## Download and Installation

Download the installer for your platform from [GitHub Releases](https://github.com/ys-ll/uniterm/releases/latest) or [Gitee Releases](https://gitee.com/ys-l/uniterm/releases):

### Windows

- **Installer** — Double-click `uniterm-windows-amd64-installer-<version>.exe` and follow the prompts to complete the installation (an arm64 installer is also available)
- **Portable** — Download `uniterm-windows-amd64-portable-<version>.zip`, extract it to any directory, and run the `uniterm.exe` inside — no installation required

### macOS

- Choose the package based on your chip: Apple Silicon (M series) uses `arm64`, Intel uses `amd64`
- Open the `.dmg` image, drag 终端 into the Applications folder, then launch it from Launchpad or the Applications folder

### Linux

- **.deb (Debian / Ubuntu, etc.)** — `sudo dpkg -i uniterm-linux-amd64-<version>.deb` or double-click to install; afterwards, launch it from the application menu
- **.rpm (Fedora / openSUSE, etc.)** — `sudo rpm -i uniterm-linux-amd64-<version>.rpm` or install with your package manager; afterwards, launch it from the application menu
- **.tar.gz (universal)** — Extract and run the `uniterm` binary inside:

  ```bash
  tar xzf uniterm-linux-amd64-<version>.tar.gz
  ./uniterm
  ```


## Creating Your First Connection

1. Open 终端, click the **+** button in the left sidebar (New Connection), or type a host address in the start page search box and choose Quick Connect.

   ![New Connection](/imgs/new_connection_light.webp)

2. In the New Connection dialog, select the protocol type (e.g., **SSH**) and fill in the connection details:
   - **Name**: Give the connection an easily recognizable name
   - **Host**: Server IP address or domain name
   - **Port**: The protocol's default port is filled in automatically
   - **Username**: Login username
   - **Password**: Login password; for other authentication methods, see [Remote Terminal](/en/connections/remote-terminal)

3. Click **Connect Only** (opens without saving) or **Save & Connect** — saved connections appear in the left-hand list.

4. Double-click a connection to open its terminal/session.


## Interface Overview

终端's main interface consists of the following areas:

- **Left Sidebar** — Tabs for Connections, Files, Monitor, Tunnels, Quick Commands, and more; see [Sidebar](/en/features/sidebar)
- **Central Terminal Area** — Terminal tabs, supporting drag-and-drop splits to form workspaces
- **Start Page** — Quick-access entry point shown at launch, with search, favorites, and recent connections


## Next Steps

- See [Start Page](/en/start-page) to learn how to use the start page
- See [Supported Protocols](/en/protocols) for all connection types
- See [Remote Terminal](/en/connections/remote-terminal) for detailed usage of SSH/Telnet/Mosh
- See [AI Assistant](/en/features/ai-assistant) to configure the AI Agent
- See [Personalization](/en/features/personalization) to adjust themes, interface font size, shortcuts, and language
- See [FAQ](/en/faq) to troubleshoot installation and connection issues
