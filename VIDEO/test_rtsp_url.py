"""RTSP URL 解析、编码与凭据脱敏单元测试。"""
import unittest

from app.utils.rtsp_url import (
    build_rtsp_auth_prefix,
    parse_rtsp_auth,
    quote_rtsp_userinfo,
    redact_url_credentials,
)


class RtspUrlTest(unittest.TestCase):
    def test_quote_rtsp_userinfo(self):
        cases = [
            ("plain", "plain"),
            ("p@ss#word", "p%40ss%23word"),
            ("a:b", "a%3Ab"),
        ]
        for password, encoded in cases:
            with self.subTest(password=password):
                self.assertEqual(encoded, quote_rtsp_userinfo(password))

    def test_build_and_parse_roundtrip_special_password(self):
        source = (
            f"rtsp://{build_rtsp_auth_prefix('admin', 'p@ss#:word')}"
            "192.168.1.64:554/Streaming/Channels/101"
        )
        auth = parse_rtsp_auth(source)
        self.assertEqual("admin", auth["username"])
        self.assertEqual("p@ss#:word", auth["password"])
        self.assertEqual("192.168.1.64", auth["hostname"])
        self.assertEqual(554, auth["port"])

    def test_redact_url_credentials(self):
        cases = [
            (
                "rtsp://admin:plain@192.168.1.64:554/Streaming/Channels/101",
                "rtsp://192.168.1.64:554/Streaming/Channels/101",
            ),
            (
                "rtsp://user:p%40ss%23word@[2001:db8::1]:8554/live?transport=tcp",
                "rtsp://[2001:db8::1]:8554/live?transport=tcp",
            ),
            ("rtmp://media.local/live/camera", "rtmp://media.local/live/camera"),
            (None, ""),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(expected, redact_url_credentials(source))


if __name__ == "__main__":
    unittest.main()
