# Roadmap

This document tracks the protocols and core features uniTerm already ships, and what we plan to build next. For per-release details, see [CHANGELOG.md](CHANGELOG.md).

Legend: ✅ Shipped, 🚧 Planned

## Protocol Support

### Terminal

| Protocol | Status | Since | Notes | Contributor |
|----------|--------|-------|-------|-------------|
| SSH | ✅ | initial release | Remote shell over SSH |  |
| Local | ✅ | v2026.05.23-alpha | Local shell (PowerShell / CMD / Git Bash / bash / zsh) |  |
| Telnet | ✅ | v2026.06.02-alpha | Remote terminal for legacy devices |  |
| Mosh | ✅ | v2026.06.02-alpha | Roaming-friendly terminal over UDP |  |
| Serial | ✅ | v1.1.0 | Serial port terminal |  |
| WSL | ✅ | v1.1.0 | Open installed WSL distributions |  |
| Raw TCP | ✅ | v1.9.0 | Raw TCP console (plain socket byte streaming) |  |

### File Transfer

| Protocol | Status | Since | Notes | Contributor |
|----------|--------|-------|-------|-------------|
| SFTP | ✅ | v2026.05.16-alpha | Dual-pane file manager over SSH |  |
| Zmodem | ✅ | v2026.06.12-alpha | In-terminal file transfer (`rz` / `sz`) |  |
| FTP / FTPS | ✅ | v2026.06.14-alpha | FTP and FTPS file transfer |  |
| SMB | ✅ | v1.2.2 | Windows shared folders and NAS |  |
| WebDAV | ✅ | v1.2.2 | WebDAV file management |  |
| S3 | ✅ | v1.2.2 | Amazon S3 compatible object storage |  |
| SCP | 🚧 | v1.9.3 | Fallback for legacy SSH servers without SFTP support |  |

### Remote Desktop

| Protocol | Status | Since | Notes | Contributor |
|----------|--------|-------|-------|-------------|
| RDP (client on Windows) | ✅ | v2026.05.22-alpha | Windows Remote Desktop |  |
| VNC | ✅ | v2026.05.23-alpha | VNC remote control |  |
| SPICE | ✅ | v2026.06.08-alpha | KVM / QEMU VM console |  |
| X11 Forwarding | ✅ | v1.7.0 | Forward remote X applications over SSH |  |
| RDP (client on macOS / Linux) | 🚧 | — | Windows Remote Desktop on macOS / Linux |  |

### Database

| Protocol | Status | Since | Notes | Contributor |
|----------|--------|-------|-------|-------------|
| MySQL | ✅ | v2026.05.27-alpha | Also covers MariaDB, TiDB, etc. |  |
| PostgreSQL | ✅ | v2026.05.27-alpha | Also covers CockroachDB, etc. |  |
| rqlite | ✅ | v2026.05.27-alpha | Distributed SQLite with Raft |  |
| Oracle | ✅ | v1.2.0 | Oracle Database | [@yuwei5380](https://github.com/yuwei5380) |
| SQL Server | ✅ | v1.2.0 | Microsoft SQL Server |  |
| Redis | ✅ | v1.2.1 | Key-value store with visual browser |  |
| MongoDB | ✅ | v1.4.1 | Document database |  |
| Elasticsearch | ✅ | v1.9.0 | Distributed search and analytics engine | [@iCarrear](https://github.com/iCarrear) |

### Container

| Protocol | Status | Since | Notes | Contributor |
|----------|--------|-------|-------|-------------|
| Kubernetes | ✅ | v1.6.0 | Kubernetes container orchestration |  |
| Docker | ✅ | v1.6.0 | Docker container runtime |  |
| nerdctl (containerd) | ✅ | v1.6.0 | containerd container runtime |  |
| Podman | ✅ | v1.6.0 | Podman container runtime |  |
| WSLC | ✅ | v1.9.0 | Windows WSL2 Container runtime | [@boltomli](https://github.com/boltomli) |

## Core Features

### AI Assistant

| Feature | Status | Since | Notes | Contributor |
|---------|--------|-------|-------|-------------|
| Anthropic Provider | ✅ | v2026.06.13-alpha | Anthropic-compatible Messages API |  |
| OpenAI Provider | ✅ | v1.1.1 | OpenAI-compatible Chat Completions API |  |
| Message Queue | ✅ | v1.4.1 | Queue messages while the agent is running |  |
| NL Database Query | ✅ | v1.4.1 | Natural-language database query generation |  |
| Multi-Panel AI Lock | ✅ | v1.5.0 | Control multiple terminals simultaneously |  |
| Skill Support | ✅ | v1.6.0 | Packaged, reusable workflows the agent can invoke | [@surenwuyuwuqiu](https://github.com/surenwuyuwuqiu) |
| Prompt Library | ✅ | v1.6.0 | Manage and trigger reusable AI prompts | [@surenwuyuwuqiu](https://github.com/surenwuyuwuqiu) |
| Interaction Modes | 🚧 | — | Chat / read-only / agent modes to constrain AI actions |  |
| MCP Server | 🚧 | — | Expose uniTerm as an MCP server for external AI agents |  |
| MCP Client | 🚧 | — | Connect external MCP servers to extend uniTerm's AI |  |
| File Attachments | 🚧 | — | Attach files to AI prompts for the agent to read |  |

### Personalization

| Feature | Status | Since | Notes | Contributor |
|---------|--------|-------|-------|-------------|
| UI Themes | ✅ | initial release | Dark / Deep Blue / Light |  |
| Terminal Themes | ✅ | initial release | Built-in terminal color themes |  |
| Internationalization | ✅ | v2026.06.10-alpha | Multi-language UI |  |
| Custom Keybindings | ✅ | v1.1.1 | Rebindable keyboard shortcuts |  |
| Background Image | ✅ | v1.5.2 | Customizable application background |  |

### Productivity

| Feature | Status | Since | Notes | Contributor |
|---------|--------|-------|-------|-------------|
| Workspace | ✅ | v2026.05.13-alpha | Split panes and broadcast input |  |
| Cloud Sync | ✅ | v2026.05.24-alpha | Encrypted sync via your own private repo |  |
| Terminal Search | ✅ | v2026.05.27-alpha | In-terminal text search |  |
| Command History | ✅ | v2026.05.29-alpha | Searchable terminal command history |  |
| Smart Completion | ✅ | v2026.05.29-alpha | Real-time command suggestions |  |
| Server Monitor | ✅ | v2026.05.29-alpha | Real-time server metrics |  |
| Text Highlighting | ✅ | v2026.06.02-alpha | Terminal text highlighting |  |
| SSH Jump Host | ✅ | v2026.06.14-alpha | Route connections through an SSH jump host |  |
| Quick Commands | ✅ | v1.0.1 | Manage and run reusable commands |  |
| Session Logging | ✅ | v1.4.0 | Log terminal output to file | [@wangxufeng](https://github.com/wangxufeng) |
| SSH Tunnel Manager | ✅ | v1.4.1 | Local, remote, and dynamic port forwarding | [@surenwuyuwuqiu](https://github.com/surenwuyuwuqiu) |
| Connection Import / Export | ✅ | v1.8.0 | Import and export connection configurations |  |

## Contributing

Have a feature to propose or a planned item you'd like to pick up? Open an issue or PR on [GitHub](https://github.com/ys-ll/uniterm/issues) — we discuss roadmap items there.
