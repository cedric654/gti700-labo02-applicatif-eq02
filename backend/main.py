import argparse
import logging
import os
import signal
import threading
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

from backend.domain import parse_rgb, team_id, topics, validate_sample
from backend.hardware import Hardware


INTERVAL_SECONDS = 3
LOG = logging.getLogger("gti700")


def broker_address(url):
    parsed = urlsplit(url)
    if parsed.scheme not in ("mqtt", "mqtts") or not parsed.hostname:
        raise ValueError("URL MQTT invalide")

    default_port = 8883 if parsed.scheme == "mqtts" else 1883
    return parsed, parsed.port or default_port


def create_client(name, url, on_connect=None, on_message=None, on_subscribe=None):
    parsed, port = broker_address(url)
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.reconnect_delay_set(min_delay=2, max_delay=2)
    if parsed.scheme == "mqtts":
        client.tls_set()
    if parsed.username:
        client.username_pw_set(
            unquote(parsed.username),
            unquote(parsed.password) if parsed.password else None,
        )

    def connected(_client, _userdata, _flags, reason_code, _properties):
        if reason_code.is_failure:
            LOG.error("[%s] connexion refusée : %s", name, reason_code)
        else:
            LOG.info("[%s] connecté", name)

    def on_disconnect(_client, _userdata, _flags, reason_code, _properties):
        if reason_code != 0:
            LOG.warning("[%s] hors ligne", name)

    client.on_connect = on_connect or connected
    client.on_disconnect = on_disconnect
    if on_message is not None:
        client.on_message = on_message
    if on_subscribe is not None:
        client.on_subscribe = on_subscribe
    client.connect_async(parsed.hostname, port, keepalive=60)
    client.loop_start()
    return client


def run(simulate=False, stopped=None):
    team = team_id(os.getenv("TEAM", "01"))
    session = os.getenv("SESSION", "E2025")
    topic = topics(team, session)
    local_url = os.getenv("LOCAL_MQTT_URL", "mqtt://127.0.0.1:1883")
    public_url = os.getenv("PUBLIC_MQTT_URL", "mqtt://broker.hivemq.com:1883")
    hardware = Hardware(simulate)
    if stopped is None:
        stopped = threading.Event()
    pending_color = [None]
    color_lock = threading.Lock()

    def on_public_connect(client, _userdata, _flags, reason_code, _properties):
        if reason_code.is_failure:
            LOG.error("[public] connexion refusée : %s", reason_code)
            return
        LOG.info("[public] connecté")
        result, _message_id = client.subscribe(topic["alert"], qos=1)
        if result != mqtt.MQTT_ERR_SUCCESS:
            LOG.error("[public] souscription aux alertes refusée")

    def on_public_subscribe(_client, _userdata, _message_id, reason_codes, _properties):
        if any(reason_code.is_failure for reason_code in reason_codes):
            LOG.error("[public] souscription aux alertes refusée")

    def on_message(_client, _userdata, message):
        if message.topic != topic["alert"] or len(message.payload) > 32:
            return
        rgb = parse_rgb(message.payload)
        if rgb is None:
            LOG.warning("Alerte RGB invalide ignorée")
            return
        with color_lock:
            pending_color[0] = rgb

    local = None
    public = None
    try:
        local = create_client("local", local_url)
        public = create_client(
            "public",
            public_url,
            on_public_connect,
            on_message,
            on_public_subscribe,
        )

        LOG.info(
            "Équipe %s — %s — période %s s",
            team,
            "SIMULATION" if simulate else "MATÉRIEL",
            INTERVAL_SECONDS,
        )
        next_read = time.monotonic()
        next_color_attempt = 0

        while not stopped.is_set():
            now = time.monotonic()

            if now >= next_color_attempt:
                with color_lock:
                    color = pending_color[0]
                    pending_color[0] = None
                if color is not None:
                    try:
                        hardware.set_color(color)
                    except Exception:
                        LOG.exception("DEL : échec de la commande")
                        with color_lock:
                            if pending_color[0] is None:
                                pending_color[0] = color
                        next_color_attempt = time.monotonic() + 2

            if now >= next_read:
                next_read = now + INTERVAL_SECONDS
                if local.is_connected():
                    try:
                        sample = validate_sample(hardware.read())
                        if local.is_connected():
                            for key in ("temperature", "humidite"):
                                info = local.publish(
                                    topic[key],
                                    f"{sample[key]:.2f}",
                                    qos=0,
                                    retain=False,
                                )
                                if info.rc != mqtt.MQTT_ERR_SUCCESS:
                                    LOG.error("Publication : %s", mqtt.error_string(info.rc))
                    except Exception:
                        LOG.exception("Capteur : échec de lecture")

            stopped.wait(0.1)
    finally:
        stopped.set()
        for client in (local, public):
            if client is not None:
                client.disconnect()
                client.loop_stop()
        hardware.close()


def main():
    parser = argparse.ArgumentParser(description="Backend MQTT GTI700")
    parser.add_argument("--simulate", action="store_true", help="simuler le capteur et la DEL")
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    stopped = threading.Event()
    signal.signal(signal.SIGINT, lambda _signum, _frame: stopped.set())
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, lambda _signum, _frame: stopped.set())

    try:
        run(args.simulate, stopped)
    except (OSError, ValueError) as error:
        LOG.error("%s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
