import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parent


class HttpEntrypointTest(unittest.TestCase):
    def test_docker_nginx_profiles_use_plain_http(self):
        for name in ('nginx.conf', 'nginx.mini.conf', 'nginx.edge.conf'):
            with self.subTest(config=name):
                config = (ROOT / 'conf' / name).read_text(encoding='utf-8')
                self.assertIn('listen 80;', config)
                self.assertNotIn('listen 443 ssl;', config)
                self.assertNotIn('ssl_certificate', config)

    def test_compose_maps_web_port_to_http_and_probes_http(self):
        compose = (ROOT / 'docker-compose.yaml').read_text(encoding='utf-8')
        self.assertIn('"${WEB_PORT:-8888}:80"', compose)
        self.assertNotIn('"${WEB_PORT:-8888}:443"', compose)
        self.assertIn('http://127.0.0.1/health', compose)
        self.assertNotIn('https://127.0.0.1/health', compose)

    def test_linux_lifecycle_does_not_require_tls_certificates(self):
        installer = (ROOT / 'install_linux.sh').read_text(encoding='utf-8')
        self.assertNotIn('ensure_ssl_certs || exit 1', installer)


if __name__ == '__main__':
    unittest.main()
