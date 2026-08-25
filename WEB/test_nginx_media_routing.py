import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parent


class NginxMediaRoutingTest(unittest.TestCase):
    def test_edge_forwarded_stream_uses_static_control_plane_srs(self):
        config = (ROOT / 'conf' / 'nginx.conf').read_text(encoding='utf-8')

        self.assertIn('proxy_pass http://srs-host:8080;', config)
        self.assertNotIn('proxy_pass http://$srs_http_upstream', config)
        self.assertNotIn('map $arg_media_node $srs_http_upstream', config)


if __name__ == '__main__':
    unittest.main()
