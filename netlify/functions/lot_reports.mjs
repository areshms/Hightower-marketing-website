// lot_reports — crowd full/open reports for trucker sleep stops (v2 function).
// POST { lot, verdict: "full"|"open" } -> aggregate
// GET  ?lots=a|b|c                     -> per-lot aggregates (7-day window)
// Store: Netlify Blobs 'hms-lot-reports' (built-in in the v2 runtime).
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

const cors = {
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET, POST',
  'access-control-allow-headers': 'content-type'
};

function json(code, obj) {
  return new Response(JSON.stringify(obj), { status: code, headers: cors });
}

export default async (req, context) => {
  const url = new URL(req.url);

  if (req.method === 'OPTIONS') return new Response('', { status: 204, headers: cors });

  let store;
  try {
    const { getStore } = await import('@netlify/blobs');
    store = getStore({ name: 'hms-lot-reports', consistency: 'strong' });
  } catch (e) {
    return json(500, { error: 'store unavailable' });
  }

  if (req.method === 'GET') {
    const lotsParam = url.searchParams.get('lots') || '';
    const lots = lotsParam.split('|').map(slugLot).filter(Boolean).slice(0, MAX_LOTS);
    if (!lots.length) return json(400, { error: 'lots ?lots=a|b|c required' });
    const out = {};
    for (const key of lots) {
      let raw = null;
      try { raw = await store.get(key); } catch { raw = null; }
      let arr = [];
      try { arr = raw ? JSON.parse(raw) : []; } catch { arr = []; }
      out[key] = aggregate(arr);
    }
    return json(200, { window_days: 7, lots: out });
  }

  if (req.method !== 'POST') return json(405, { error: 'GET or POST only' });

  let body = {};
  try { body = JSON.parse((await req.text()).slice(0, MAX_BODY)); } catch { body = {}; }
  const key = slugLot(body.lot);
  if (!key) return json(400, { error: 'lot required' });
  if (!['full', 'open'].includes(String(body.verdict))) return json(400, { error: 'verdict must be full|open' });

  try {
    const raw = await store.get(key);
    let arr = [];
    try { arr = raw ? JSON.parse(raw) : []; } catch { arr = []; }
    const now = Date.now();
    arr.push({ t: now, v: String(body.verdict) });
    arr = arr.filter((r) => now - r.t <= DAY_MS).slice(-40);
    await store.setJSON(key, arr);
    return json(200, { ok: true, lot: key, ...aggregate(arr) });
  } catch (e) {
    return json(500, { error: 'store write failed' });
  }
};

export const config = { path: '/.netlify/functions/lot_reports' };
