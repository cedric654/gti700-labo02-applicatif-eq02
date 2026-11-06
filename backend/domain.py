import math
import re

RGB_PATTERN = re.compile(r"[0-9]{1,3};[0-9]{1,3};[0-9]{1,3}")


def team_id(value):
    text = str(value)
    if not re.fullmatch(r"\d{1,2}", text) or int(text) < 1:
        raise ValueError("Équipe attendue : 01 à 99")
    return text.zfill(2)


def topics(team, session):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", session):
        raise ValueError("Session invalide")

    team = team_id(team)
    data = f"GTI700/Data/{session}/{team}"
    return {
        "temperature": f"{data}/temperature",
        "humidite": f"{data}/humidite",
        "alert": f"GTI700/Alerts/{session}/{team}",
    }


def parse_rgb(payload):
    try:
        text = payload.decode("ascii") if isinstance(payload, bytes) else str(payload)
        text = text.strip()
        if not RGB_PATTERN.fullmatch(text):
            return None

        rgb = tuple(int(part) for part in text.split(";"))
        return rgb if all(value <= 255 for value in rgb) else None
    except (UnicodeDecodeError, ValueError):
        return None


def validate_sample(sample):
    if not isinstance(sample, dict):
        raise ValueError("Mesure attendue : deux nombres")

    values = {}
    for key in ("temperature", "humidite"):
        value = sample.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Mesure invalide : {key}")
        if not math.isfinite(value):
            raise ValueError(f"Mesure invalide : {key}")
        if key == "humidite" and not 0 <= value <= 100:
            raise ValueError(f"Mesure invalide : {key}")
        values[key] = value
    return values
