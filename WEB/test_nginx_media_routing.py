import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parent


class NginxMediaRoutingTest(unittest.TestCase):
    def test_edge_forwarded_stream_uses_static_control_plane_srs(self):
        config = (ROOT / 'conf' / 'nginx.conf').read_text(encoding='utf-8')

        self.assertIn('proxy_pass http://srs-host:8080;', config)
        self.assertNotIn('proxy_pass http://$srs_http_upstream', config)
        self.assertNotIn('map $arg_media_node $srs_http_upstream', config)

    def test_mini_routes_only_public_branding_reads_to_infra_without_token(self):
        config = (ROOT / 'conf' / 'nginx.mini.conf').read_text(encoding='utf-8')
        common_headers = (
            'proxy_set_header Host $host;',
            'proxy_set_header X-Real-IP $remote_addr;',
            'proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;',
            'proxy_set_header X-Forwarded-Proto $scheme;',
            'proxy_set_header Authorization "";',
        )

        for api_prefix in ('admin-api', 'dev-api'):
            generic_location = f'location ^~ /{api_prefix}/ {{'
            public_locations = (
                f'location = /{api_prefix}/infra/platform-branding/get {{',
                f'location ^~ /{api_prefix}/infra/platform-branding/image/ {{',
            )
            for declaration in public_locations:
                with self.subTest(location=declaration):
                    start = config.index(declaration)
                    end = config.index('\n        }', start)
                    block = config[start:end]

                    self.assertLess(start, config.index(generic_location))
                    for header in common_headers:
                        self.assertIn(header, block)
                    self.assertIn('set $infra_upstream iot-infra:48082;', block)
                    self.assertIn('proxy_pass http://$infra_upstream;', block)
                    if api_prefix == 'dev-api':
                        self.assertIn('rewrite ^/dev-api/(.*)$ /admin-api/$1 break;', block)
                        self.assertLess(block.index('set $infra_upstream'), block.index('rewrite '))

        # No trailing slash: the authenticated image upload must stay on the generic system route.
        self.assertNotIn('location = /admin-api/infra/platform-branding/image {', config)
        self.assertNotIn('location = /dev-api/infra/platform-branding/image {', config)


if __name__ == '__main__':
    unittest.main()
