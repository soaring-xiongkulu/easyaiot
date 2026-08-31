import unittest

from app.services.vehicle_identity_service import normalize_plate_no, _normalize_color


class VehicleIdentityNormalizationTest(unittest.TestCase):
    def test_plate_normalization(self):
        self.assertEqual(normalize_plate_no(' 粤 b·12345 '), '粤B12345')
        self.assertEqual(normalize_plate_no('粤B-12345'), '粤B12345')

    def test_plate_color_normalization(self):
        self.assertEqual(_normalize_color('蓝色'), 'blue')
        self.assertEqual(_normalize_color('BLUE'), 'blue')
        self.assertIsNone(_normalize_color(None))


if __name__ == '__main__':
    unittest.main()
