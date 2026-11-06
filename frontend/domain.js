/* Partagé entre la page autonome et les outils locaux. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.Lab = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  function teamId(value) {
    const text = String(value);
    if (!/^\d{1,2}$/.test(text) || Number(text) < 1) throw new Error('Équipe attendue : 01 à 99');
    return text.padStart(2, '0');
  }
  function topics(team, session = 'E2025') {
    if (!/^[A-Za-z0-9_-]+$/.test(session)) throw new Error('Session invalide');
    const id = teamId(team);
    const data = `GTI700/Data/${session}/${id}`;
    return { temperature: `${data}/temperature`, humidite: `${data}/humidite`,
      alert: `GTI700/Alerts/${session}/${id}`, alerts: `GTI700/Alerts/${session}/+` };
  }
  function parseRgb(payload) {
    const text = String(payload).trim();
    if (!/^[0-9]{1,3};[0-9]{1,3};[0-9]{1,3}$/.test(text)) return null;
    const rgb = text.split(';').map(Number);
    return rgb.every(v => v <= 255) ? rgb : null;
  }
  function measurement(payload, kind) {
    const text = String(payload).trim();
    if (!/^-?\d+(?:\.\d+)?$/.test(text)) return null;
    const value = Number(text);
    if (!Number.isFinite(value) || !['temperature', 'humidite'].includes(kind)) return null;
    if (kind === 'humidite' && (value < 0 || value > 100)) return null;
    return value;
  }
  function validateSample(sample) {
    if (!sample || typeof sample.temperature !== 'number' || typeof sample.humidite !== 'number')
      throw new Error('Mesure attendue : deux nombres');
    for (const key of ['temperature', 'humidite']) {
      if (measurement(sample[key], key) === null) throw new Error(`Mesure invalide : ${key}`);
    }
    return sample;
  }
  // Les topics imposés ne transportent aucun identifiant de mesure.
  // Appariement approximatif dans une fenêtre de 1 s, sans réutiliser une ancienne valeur.
  class History {
    constructor(limit = 15, pairWindow = 1000) {
      this.rows = []; this.limit = limit; this.pairWindow = pairWindow;
    }
    add(kind, value, now = Date.now()) {
      if (measurement(value, kind) === null) return false;
      let row = this.rows[this.rows.length - 1];
      if (!row || now - row.time > this.pairWindow || row[kind] !== null) {
        row = {time: now, temperature: null, humidite: null};
        this.rows.push(row);
        if (this.rows.length > this.limit) this.rows.shift();
      }
      row[kind] = Number(value);
      return true;
    }
    clear() { this.rows = []; }
  }
  return {teamId, topics, parseRgb, measurement, validateSample, History};
});
