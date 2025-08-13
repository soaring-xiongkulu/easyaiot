import os
import sys
from contextlib import contextmanager

import psutil


def get_disks() -> list[str]:
    return [disk.mountpoint for disk in psutil.disk_partitions(all=False) if
            disk.fstype in ('ext4', 'overlay') and disk.mountpoint != '/var/log.hdd']

def get_disk_path(file_path) -> str:
    disks = get_disks()
    match_str_count = [len(disk) if file_path.find(disk) == 0 else -1 for disk in disks]
    return disks[match_str_count.index(max(match_str_count))]

def get_disk_usage(disk_or_file_path: str):
    return psutil.disk_usage(get_disk_path(disk_or_file_path))

_devnull = open(os.devnull, 'wb')

@contextmanager
def suppress_stderr():
    original_stderr_fd = sys.stderr.fileno()
    saved_stderr_fd = os.dup(original_stderr_fd)
    os.dup2(_devnull.fileno(), original_stderr_fd)
    yield
    os.dup2(saved_stderr_fd, original_stderr_fd)
    os.close(saved_stderr_fd)

def check_ip_reachable(ip: str) -> bool:
    return os.system(f'ping -w 1 {ip} >/dev/null 2>&1') == 0