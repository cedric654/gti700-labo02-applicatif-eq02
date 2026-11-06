/* global Lab, mqtt */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const config = window.LAB_CONFIG;
  const clients = [];
  let freshnessTimer;
  try {
    if (typeof mqtt === 'undefined') throw new Error('Client MQTT absent : exécutez npm install dans frontend/.');
    if (!Number.isInteger(config.teamCount) || config.teamCount < 1 || config.teamCount > 99)
      throw new Error('teamCount doit être compris entre 1 et 99.');
    if (Number(Lab.teamId(config.team)) > config.teamCount) throw new Error('L’équipe dépasse teamCount.');
    if (!Number.isFinite(config.staleAfterMs) || config.staleAfterMs < 3000) throw new Error('Délai de péremption invalide.');
    for (const url of [config.localUrl, config.publicUrl]) {
      if (!['ws:', 'wss:'].includes(new URL(url).protocol)) throw new Error('Le navigateur exige WebSocket.');
    }
    const topics = Lab.topics(config.team, config.session);
    const history = new Lab.History(15);
    const received = {temperature: 0, humidite: 0};
    $('identity').textContent = `Équipe ${Lab.teamId(config.team)} · ${config.session}`;
    const alertCells = new Map();
    for (let i = 1; i <= config.teamCount; i++) {
      const row = document.createElement('tr');
      const team = document.createElement('th'); team.scope = 'row'; team.textContent = String(i);
      const cell = document.createElement('td'); cell.className = 'swatch';
      cell.setAttribute('aria-label', 'Aucune alerte reçue'); cell.title = 'Aucune alerte reçue';
      row.append(team, cell); $('alerts').append(row); alertCells.set(Lab.teamId(i), cell);
    }
    function render() {
      const fragment = document.createDocumentFragment();
      for (const row of history.rows) {
        const tr = document.createElement('tr');
        if (Date.now() - row.time > config.staleAfterMs) tr.className = 'stale';
        const values = [new Date(row.time).toLocaleTimeString('fr-CA'),
          row.temperature === null ? '—' : `${row.temperature.toFixed(2)} °C`,
          row.humidite === null ? '—' : `${row.humidite.toFixed(2)} %`];
        values.forEach(value => { const td = document.createElement('td'); td.textContent = value; tr.append(td); });
        fragment.append(tr);
      }
      $('sensors').replaceChildren(fragment);
      const stale = Object.keys(received).filter(key => Date.now() - received[key] > config.staleAfterMs);
      $('freshness').textContent = stale.length ? `Mesures absentes ou périmées : ${stale.join(', ')}.` : 'Mesures à jour.';
    }
    function connect(url, statusId, subscriptions, onMessage, onOffline) {
      const status = $(statusId);
      const prefix = statusId === 'local-status' ? 'Local' : 'Public';
      const client = mqtt.connect(url, {clean: true, reconnectPeriod: 2000, connectTimeout: 10000, resubscribe: false});
      clients.push(client);
      function state(text, online = false) { status.textContent = `${prefix} : ${text}`; status.className = online ? 'online' : ''; }
      client.on('connect', () => {
        client.subscribe(subscriptions, {qos: 0}, (error, grants) => {
          if (error || grants?.some(g => g.qos === 128)) state('souscription refusée');
          else state('connecté', true);
        });
      });
      client.on('offline', () => { state('hors ligne'); if (onOffline) onOffline(); });
      client.on('reconnect', () => state('reconnexion…'));
      client.on('error', error => { state('erreur'); $('error').textContent = `${prefix} : ${error.message}`; });
      client.on('message', (topic, payload) => {
        if (payload.length <= 64) onMessage(topic, payload.toString());
      });
      return client;
    }
    connect(config.localUrl, 'local-status', [topics.temperature, topics.humidite], (topic, payload) => {
      const kind = topic === topics.temperature ? 'temperature' : topic === topics.humidite ? 'humidite' : null;
      if (!kind) return;
      const value = Lab.measurement(payload, kind);
      if (value === null) return;
      received[kind] = Date.now(); history.add(kind, value); render();
    }, () => { history.clear(); received.temperature = received.humidite = 0; render(); });
    const prefix = `GTI700/Alerts/${config.session}/`;
    connect(config.publicUrl, 'public-status', topics.alerts, (topic, payload) => {
      if (!topic.startsWith(prefix)) return;
      const cell = alertCells.get(topic.slice(prefix.length));
      const rgb = Lab.parseRgb(payload);
      if (!cell || !rgb) return;
      cell.style.background = `rgb(${rgb.join(',')})`;
      cell.title = `${rgb.join(';')} · ${new Date().toLocaleTimeString('fr-CA')}`;
      cell.setAttribute('aria-label', cell.title);
    });
    freshnessTimer = setInterval(render, 1000);
    render();
  } catch (error) {
    $('error').textContent = error.message;
    clients.forEach(client => client.end(true));
  }
  window.addEventListener('beforeunload', () => {
    clearInterval(freshnessTimer); clients.forEach(client => client.end(true));
  });
})();
