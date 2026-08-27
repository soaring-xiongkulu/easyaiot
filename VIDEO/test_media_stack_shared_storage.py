import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / '.scripts' / 'media-cluster' / 'install_media_stack.sh'


class SharedStorageGuardTest(unittest.TestCase):
    def run_guard(self, fs_type: str):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            mount = root / 'media'
            mount.mkdir()
            fake_bin = root / 'bin'
            fake_bin.mkdir()
            findmnt = fake_bin / 'findmnt'
            findmnt.write_text(
                '#!/usr/bin/env bash\n'
                'if [[ "$*" == *"FSTYPE"* ]]; then printf "%s\\n" "$FAKE_FS_TYPE"; '
                'else printf "fake-source\\n"; fi\n',
                encoding='utf-8',
            )
            findmnt.chmod(findmnt.stat().st_mode | stat.S_IXUSR)
            env = dict(os.environ)
            env.update({
                'PATH': f'{fake_bin}:{env.get("PATH", "")}',
                'FAKE_FS_TYPE': fs_type,
                'MEDIA_NODE_HOST': '127.0.0.1',
                'MEDIA_RECORDING_ROOT': str(mount),
                'REQUIRE_SHARED_STORAGE_MOUNT': '1',
            })
            return subprocess.run(
                ['bash', '-c', f'source "{SCRIPT}"; ensure_ceph_mount'],
                env=env,
                capture_output=True,
                text=True,
            )

    def test_rejects_writable_ext4_directory(self):
        result = self.run_guard('ext4')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('不是中心共享存储', result.stderr)

    def test_accepts_nfs_mount(self):
        result = self.run_guard('nfs4')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('共享存储已挂载', result.stdout)


if __name__ == '__main__':
    unittest.main()
