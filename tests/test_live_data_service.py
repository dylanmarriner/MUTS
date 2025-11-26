"""Tests for the LiveDataService."""
import unittest
from unittest.mock import MagicMock

from diagnostics.live_data_service import LiveDataService, LiveData


class TestLiveDataService(unittest.TestCase):
    def test_read_all_live_data(self):
        # Arrange
        uds_client = MagicMock()

        def read_data_by_id_side_effect(did):
            if did == 0x0C:
                return b'\x1a\x90'  # 6800 RPM
            if did == 0x11:
                return b'\x01\xf4'  # 500 (50.0%)
            if did == 0x04:
                return b'\x01\x2c'  # 300 (30.0%)
            if did == 0x70:
                return b'\x01\x9a'  # 410 (41.0 kPa)
            if did == 0x5A:
                return b'\x04\x1a'  # 1050 (105.0 psi)
            if did == 0x0E:
                return b'\x00\xfa'  # 250 (25.0 deg)
            if did == 0x0F:
                return b'\x00\x50'  # 80 (40C)
            if did == 0x05:
                return b'\x00\x5a'  # 90 (50C)
            if did == 0x0D:
                return b'\x00\x64'  # 100 (100 kph)
            return b'\x00\x00'

        uds_client.read_data_by_id.side_effect = read_data_by_id_side_effect

        live_data_service = LiveDataService(uds_client)

        # Act
        live_data = live_data_service.read_all_live_data()

        # Assert
        self.assertIsInstance(live_data, LiveData)
        self.assertEqual(live_data.rpm, 6800)
        self.assertAlmostEqual(live_data.throttle, 50.0)
        self.assertAlmostEqual(live_data.engine_load, 3.0)
        self.assertAlmostEqual(live_data.boost_psi, 5.946558)
        self.assertAlmostEqual(live_data.fuel_pressure_psi, 152.2899)
        self.assertAlmostEqual(live_data.ignition_advance_deg, 25.0)
        self.assertEqual(live_data.iat_c, 40)
        self.assertEqual(live_data.ect_c, 50)
        self.assertEqual(live_data.vehicle_speed_kph, 100)


if __name__ == '__main__':
    unittest.main()
