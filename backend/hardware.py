import logging
import math
import os


class Hardware:
    def __init__(self, simulate=False):
        self.simulate = simulate
        self.count = 0
        self.sensor = None
        self.led = None

    def read(self):
        if self.simulate:
            self.count += 1
            return {
                "temperature": 22 + math.sin(self.count / 5),
                "humidite": 45 + math.cos(self.count / 7) * 3,
            }

        if self.sensor is None:
            self.sensor = self._open_sensor()
        return {
            "temperature": self.sensor.temperature,
            "humidite": self.sensor.humidity,
        }

    def set_color(self, rgb):
        if self.simulate:
            logging.info("[DEL simulée] %s", ";".join(map(str, rgb)))
            return

        if self.led is None:
            self.led = self._open_led()
        self.led.color = tuple(value / 255 for value in rgb)

    def close(self):
        if self.sensor is not None:
            self.sensor.exit()
        if self.led is not None:
            self.led.off()
            self.led.close()

    @staticmethod
    def _open_sensor():
        import adafruit_dht
        import board

        model = os.getenv("DHT_MODEL", "DHT11")
        if model not in ("DHT11", "DHT22"):
            raise ValueError("DHT_MODEL doit être DHT11 ou DHT22")
        pin = getattr(board, "D" + os.getenv("DHT_PIN", "17"))
        return getattr(adafruit_dht, model)(pin, use_pulseio=False)

    @staticmethod
    def _open_led():
        from gpiozero import RGBLED

        pins = [
            int(os.getenv(name, default))
            for name, default in (
                ("LED_RED_PIN", "22"),
                ("LED_GREEN_PIN", "23"),
                ("LED_BLUE_PIN", "24"),
            )
        ]
        if len(set(pins)) != 3 or int(os.getenv("DHT_PIN", "17")) in pins:
            raise ValueError("Les broches des périphériques doivent être distinctes")

        active_high = os.getenv("LED_ACTIVE_HIGH", "true").lower()
        if active_high not in ("true", "false"):
            raise ValueError("LED_ACTIVE_HIGH doit être true ou false")
        return RGBLED(
            *pins,
            active_high=active_high == "true",
            initial_value=(0, 0, 0),
        )
