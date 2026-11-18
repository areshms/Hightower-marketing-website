// lot_reports — crowd full/open reports for trucker sleep stops.
// POST { lot, verdict: "full"|"open" } -> aggregate
// GET  ?lots=a|b|c                     -> per-lot aggregates (7-day window)
// Store: Netlify Blobs 'hms-lot-reports' (runtime-provided, no extra creds).
const DAY_MS = 7 * 24 * 60 * 60 * 1000;
const MAX_LOTS = 24;
const MAX_BODY = 2000;

function slugLot(name) {
  return String(name || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80);
}

function aggregate(arr) {
  const now = Date.now();
  const fresh = (arr || []).filter((r) => now - r.t <= DAY_MS);
  return {
    full: fresh.filter((r) => r.v === 'full').length,
    open: fresh.filter((r) => r.v === 'open').length,
    total: fresh.length,
    last_ts: fresh.length ? fresh[fresh.length - 1].t : null
  };
}

exports.handler = async (event) => {
  const cors = {
    'access-control-allow-origin': '*',
    'access-control-allow-methods': 'GET, POST',
    'access-control-allow-headers': 'content-type'
  };

  if (event.httpMethod === 'OPTIONS') return { statusCode: 204, headers: cors, body: '' };

  let store;
  try {
    const blobs = require('@netlify/blobs');
    store = blobs.getStore({ name: 'hms-lot-reports', consistency: 'strong' });
  } catch (e) {
    return { statusCode: 500, headers: cors, body: JSON.stringify({ error: 'store unavailable' }) };
  }

  if (event.httpMethod === 'GET') {
    const lotsParam = (event.queryStringParameters || {}).lots || '';
    const lots = lotsParam.split('|').map(slugLot).filter(Boolean).slice(0, MAX_LOTS);
    if (!lots.length) return { statusCode: 400, headers: cors, body: JSON.stringify({ error: 'lots ?lots=a|b|c required' }) };
    const out = {};
    for (const key of lots) {
      let arr = [];
      try {
        const raw = await store.get(key);
        arr = raw ? JSON.parse(raw) : [];
      } catch { arr = []; }
      out[key] = aggregate(arr);
    }
    return { statusCode: 200, headers: cors, body: JSON.stringify({ window_days: 7, lots: out }) };
  }

  if (event.httpMethod !== 'POST') return { statusCode: 405, headers: cors, body: JSON.stringify({ error: 'GET or POST only' }) };

  let body = {};
  try { body = JSON.parse((event.body || '').slice(0, MAX_BODY)); } catch { body = {}; }
  const key = slugLot(body.lot);
  if (!key) return { statusCode: 400, headers: cors, body: JSON.stringify({ error: 'lot required' }) };
  if (!['full', 'open'].includes(body.verdict)) return { statusCode: 400, headers: cors, body: JSON.stringify({ error: 'verdict must be full|open' }) };

  try {
    const raw = await store.get(key);
    let arr = [];
    try { arr = raw ? JSON.parse(raw) : []; } catch { arr = []; }
    const now = Date.now();
    arr.push({ t: now, v: body.verdict });
    arr = arr.filter((r) => now - r.t <= DAY_MS).slice(-40);
    await store.setJSON(key, arr);
    return { statusCode: 200, headers: cors, body: JSON.stringify(Object.assign({ ok: true, lot: key }, aggregate(arr))) };
  } catch (e) {
    return { statusCode: 500, headers: cors, body: JSON.stringify({ error: 'store write failed' }) };
  }
};
