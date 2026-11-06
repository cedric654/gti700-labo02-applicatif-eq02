import unittest

from backend.domain import parse_rgb, team_id, topics, validate_sample
from backend.hardware import Hardware


class DomainTests(unittest.TestCase):
    def test_team_and_topics(self):
        self.assertEqual(team_id("7"), "07")
        self.assertEqual(
            topics("7", "E2025")["alert"],
            "GTI700/Alerts/E2025/07",
        )
        with self.assertRaises(ValueError):
            team_id("0")
        with self.assertRaises(ValueError):
            topics("01", "bad/session")

    def test_rgb(self):
        self.assertEqual(parse_rgb(b"255;0;30"), (255, 0, 30))
        for payload in (b"256;0;0", b"1;2", b"red;0;0", b"\xff"):
            self.assertIsNone(parse_rgb(payload))

    def test_sample(self):
        self.assertEqual(
            validate_sample({"temperature": 22, "humidite": 45}),
            {"temperature": 22, "humidite": 45},
        )
        for sample in (
            {"temperature": float("nan"), "humidite": 45},
            {"temperature": 22, "humidite": 101},
            {"temperature": True, "humidite": 45},
        ):
            with self.assertRaises(ValueError):
                validate_sample(sample)


class SimulationTests(unittest.TestCase):
    def test_simulated_hardware(self):
        hardware = Hardware(simulate=True)
        first = hardware.read()
        second = hardware.read()

        self.assertNotEqual(first, second)
        self.assertTrue(0 <= first["humidite"] <= 100)
        hardware.set_color((255, 0, 0))
        hardware.close()


if __name__ == "__main__":
    unittest.main()
