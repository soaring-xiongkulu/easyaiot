# Supported Protocols

终端 supports 30+ connection protocols, covering remote terminals, remote desktops, file transfers, databases, containers, and server monitoring.

## Remote Terminal

| Protocol | Default Port | Description |
|------|----------|------|
| SSH | 22 | Encrypted remote shell with password/key authentication and tunnel forwarding |
| Telnet | 23 | Plaintext remote terminal, suitable for embedded devices and legacy systems |
| Mosh | 22 (SSH) | UDP-based mobile shell, ideal for high-latency networks |
| Raw TCP | Custom | Raw TCP console that connects directly to a host port and transceives raw bytes |

## Local Connections

| Type | Description |
|------|------|
| Local Shell | PowerShell, CMD, Clink, Cygwin, MSYS2, Nushell, elevated (administrator) terminal (Windows), bash, zsh, and more |
| WSL | Windows Subsystem for Linux, opens installed Linux distributions |
| Serial | Serial port connection, configurable baud rate, data bits, stop bits, and parity |

## Remote Desktop

| Protocol | Default Port | Description |
|------|----------|------|
| RDP | 3389 | Windows Remote Desktop |
| VNC | 5900 | Linux remote control |
| SPICE | 5900 | KVM/QEMU virtual machine desktop |
| X11 | 22 (SSH) | Remote Linux GUI applications and desktop environments |

## File Transfer

| Protocol | Default Port | Description |
|------|----------|------|
| SFTP | 22 (SSH) | SSH-based secure file transfer |
| SCP | 22 (SSH) | SSH-based file transfer, compatible with servers that lack an SFTP subsystem (SSH connections can choose between SFTP / SCP) |
| FTP / FTPS | 21 | Traditional file transfer and its encrypted version |
| SMB | 445 | Windows file sharing |
| WebDAV | 80 / 443 | HTTP-based file management |
| S3 | Custom | S3 API-compatible object storage |
| Zmodem | - (within SSH terminals) | `rz`/`sz` transfers inside SSH terminals, with a configurable default download directory |
| WSL Files | //wsl.localhost | Browse and manage files of Windows WSL distributions |

## Server Monitor

| Type | Connection | Description |
|------|----------|------|
| Monitor | SSH | CPU / memory / network / disk / process monitoring with port and hardware details; Service Management, Hardware Devices, and IPMI tabs |

## Databases

| Database | Default Port | Description |
|--------|----------|------|
| MySQL | 3306 | MySQL wire protocol compatible: MySQL, MariaDB, TiDB, and more |
| PostgreSQL | 5432 | PostgreSQL wire protocol compatible: PostgreSQL, CockroachDB, and more |
| Oracle | 1521 | Oracle Database via pure Go driver |
| SQL Server | 1433 | SQL Server via pure Go driver |
| rqlite | 4001 | Lightweight distributed database built on SQLite with Raft consensus |
| Redis | 6379 | In-memory key-value database with visual key browsing and editing |
| MongoDB | 27017 | Document database with tree browsing, queries, and inline editing |
| Elasticsearch | 9200 | Distributed search and analytics engine with index and document management |

## Containers

| Type | Connection | Description |
|------|----------|------|
| Kubernetes | kubeconfig (optional SSH tunnel) | Cluster resource browsing and management, YAML editing, Pod logs and exec terminals, CPU/memory metrics |
| Docker | Local / remote over SSH | Container and image management with lifecycle actions, logs, exec, and image pull |
| Podman | Local / remote over SSH | Docker-compatible container engine with container and image management |
| nerdctl (containerd) | Local / remote over SSH | containerd container management with namespace switching |
| WSLC | Windows WSL2 | Windows WSL2 Container runtime |
