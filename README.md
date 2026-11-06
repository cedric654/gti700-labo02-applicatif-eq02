# GTI700 — Laboratoire 2

Capteurs et alertes MQTT avec un backend Python, géré par uv, et un front-end HTML autonome.

## Installation

Installer [uv](https://docs.astral.sh/uv/) et Node.js/npm (utilisés uniquement pour les outils du front-end et la démonstration locale).

```bash
cp .env.example .env
uv sync --project backend
npm --prefix frontend install
```

Le front-end ouvre directement `frontend/index.html`; npm y installe le client MQTT navigateur et le copie dans `frontend/vendor/`.

## Lancement

```bash
uv run --project backend python -m backend.main
```

Sans Raspberry Pi, lancez le mode simulation :

```bash
uv run --project backend python -m backend.main --simulate
```

Le backend publie les mesures sur le courtier local et applique les alertes reçues sur le courtier public. Le navigateur se connecte aux deux courtiers par WebSocket.

## Démonstration locale

1. Dans `.env`, définir `PUBLIC_MQTT_URL=mqtt://127.0.0.1:1884`.
2. Dans `frontend/config.js`, utiliser `ws://127.0.0.1:9001` pour le courtier local et `ws://127.0.0.1:9002` pour le public.
3. Démarrer les courtiers privés : `npm --prefix frontend run demo:brokers`.
4. Dans un autre terminal, lancer le backend avec `--simulate`.
5. Ouvrir `frontend/index.html`.

Cette démonstration n’utilise pas HiveMQ. Fermer les deux programmes avec Ctrl+C.

## Raspberry Pi

Installer Mosquitto et configurer son listener MQTT local (1883) et son listener WebSocket (9001). Créer l’environnement uv et installer les dépendances matérielles :

```bash
uv sync --project backend --extra hardware
```

Vérifier le câblage avant d’utiliser les valeurs par défaut. Les broches sont en numérotation BCM; adapter `DHT_MODEL`, `DHT_PIN`, `LED_RED_PIN`, `LED_GREEN_PIN`, `LED_BLUE_PIN` et `LED_ACTIVE_HIGH` dans `.env`. Ne pas exposer le listener anonyme du laboratoire à Internet.

Configurer `TEAM`, `SESSION`, les URL MQTT dans `.env`, puis les URL WebSocket et `teamCount` dans `frontend/config.js`. Lancer le backend sans `--simulate` et ouvrir `frontend/index.html`.

## Topics

| Courtier | Topic | Charge utile |
|---|---|---|
| Local | `GTI700/Data/E2025/XX/temperature` | Nombre à deux décimales |
| Local | `GTI700/Data/E2025/XX/humidite` | Nombre à deux décimales |
| Public | `GTI700/Alerts/E2025/XX` | RGB sous la forme `255;0;128` |
| Public | `GTI700/Alerts/E2025/+` | Filtre d’alertes du navigateur |

Le backend valide les mesures et les alertes, ne publie pas lorsque le courtier local est hors ligne, et réessaie la connexion MQTT. Le navigateur garde les 15 dernières lignes.

Les scripts `humid.py` et `intelligent_measur.py` du cours n’étaient pas fournis. Le matériel pris en charge par défaut est un DHT11/DHT22 et une DEL RGB branchée sur trois GPIO PWM; confirmer le modèle et les broches avec le kit avant utilisation.

Consulter [docs/DEMONSTRATION.md](./docs/DEMONSTRATION.md), [docs/VALIDATION.md](./docs/VALIDATION.md) et [docs/RAPPORT.md](./docs/RAPPORT.md) pour les vérifications et le rapport.
