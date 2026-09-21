# About 终端

终端 is a lightweight all-in-one terminal emulator supporting **30+** connection protocols, covering remote terminals, remote desktops, file transfers, database management, containers, and server monitoring. It ships with a built-in **autonomous AI Agent** that can independently plan and execute multi-round shell commands.


## Core Features

### All-in-One Terminal

Cover all your remote access needs and get everything done in a single application.

#### Remote Terminal

Connect to **SSH** servers with authentication via Keystore, password, key, Kerberos (GSSAPI), or SSH Agent, with agent forwarding support. Any connection can be routed through an SSH jump host. Also supports **Telnet** and **Mosh** (ideal for high-latency, intermittent network environments).

![New Connection](/imgs/new_connection_light.webp)

#### Local and Serial Terminal

Supports **PowerShell / CMD / Git Bash / Cygwin / MSYS2 / Nushell / WSL** local terminals and **elevated (administrator) terminals**, a **Raw TCP** console, and **serial** connections with configurable baud rate, data bits, stop bits, and parity.

#### File Transfer

Built-in **SFTP / SCP / FTP / FTPS / SMB / WebDAV / S3** dual-pane file browser and file sidebar, with **WSL file management**, **Zmodem** (`rz`/`sz`), and unified transfer tasks (failed-transfer retry, per-file details).

![SFTP](/imgs/sftp_light.webp)

#### Remote Desktop

Integrated **RDP** (Windows Remote Desktop), **VNC** (Linux remote control), and **SPICE** (KVM/QEMU virtual machine) protocols provide a smooth graphical remote desktop experience.

![RDP](/imgs/rdp_light.webp)

#### Database Client

Supports **MySQL / PostgreSQL / Oracle / SQL Server / rqlite / Redis / MongoDB / Elasticsearch**, with inline editing, query history, result export, and script execution.

![Database](/imgs/database_light.webp)

#### Containers

Integrated **Kubernetes / Docker / Podman / nerdctl / WSLC** management for cluster resources and container images on the local machine or remote hosts over SSH — with lifecycle actions, log following, and exec into a container terminal.

![Kubernetes](/imgs/kubernetes_light.webp)

#### Server Monitor

Monitor CPU / memory / network / disk and processes on remote hosts in real time, with port, disk, and network-adapter details, plus **service management, hardware devices, IPMI** sensors, and host clock drift detection.

#### Sidebar

Companion panels for Files, Monitor, Tunnels, Quick Commands, and more stay alongside your terminals. The file sidebar can follow the terminal's working directory and supports WSL file browsing.


### AI Assistant

终端 ships with a built-in autonomous AI Agent that can independently plan and execute multi-round shell commands in the terminal.

- **Autonomous Multi-Round Execution** — The AI Agent plans, executes, observes results, and iterates across multiple rounds without human intervention.
- **LLM Integration** — The sidebar chat supports Anthropic/OpenAI-compatible APIs, so you can use Claude, GPT, and other compatible models.
- **Flexible Execution Modes** — Confirm all, confirm write commands, confirm dangerous commands, or confirm nothing — you control the level of supervision over the AI Agent.
- **Persistent Conversations** — Conversation history is saved per session and survives application restarts; sessions can be renamed and exported as Markdown.
- **In-Terminal Integration** — AI commands run directly in the active terminal tab, either pinned to a specific terminal or always following the active tab.
- **Skills & Commands** — Capture reusable workflows as **skills** (which the AI can invoke on its own) and parameterized prompts as **commands**, invoked quickly in the conversation via `/name`.
- **Smart Completion** — Receive real-time suggestions from command history and AI while typing in SSH terminals.

![AI Assistant](/imgs/ai_assistant_light.webp)


### Personalization

#### Connection Management

Group, search, create, and batch-manage server connections, with frequently used connections **pinned as favorites**. One-click import from Xshell, MobaXterm, DBeaver, Navicat, and more — everything at your fingertips.

#### Keystore & Proxies

Centrally manage reusable login credentials (passwords / private keys) and SOCKS5 / HTTP proxies. Reference them directly when connecting and sync them across devices.

#### Workspaces and Splits

Drag and drop terminal tabs into the content area to freely split panes and combine them into workspaces; drag panel edges to resize and rearrange, with panel maximizing and app-wide input broadcasting.

![Workspace](/imgs/workspace_light.webp)

#### Cloud Sync

Encrypted sync of connections, favorites, and AI settings via your own GitHub / GitLab / Gitee private repository — no worries about data loss or leaks, seamlessly transition across devices.

![Cloud Sync](/imgs/cloud_sync_light.webp)

#### In-App Updates

Automatic failover between GitHub and Gitee sources — download, verify, and install updates in one click within the app.

#### Custom Keyboard Shortcuts

Freely bind keyboard shortcuts for nearly every operation, so your hands never need to leave the keyboard.

#### Themes

A variety of terminal themes and UI themes, with customizable interface font size, font family, and colors.

![Terminal Settings](/imgs/terminal_settings_light.webp)

#### Multi-Language

9 interface languages: Simplified Chinese, Traditional Chinese, English, 日本語, 한국어, Deutsch, Español, Français, Русский.


## Next Steps

- [Getting Started](/en/getting-started) — Download, install, and establish your first connection
- [Connection Protocols](/en/connections/remote-terminal) — Learn how to use each protocol
- [Feature Guide](/en/features/ai-assistant) — Explore features in depth
