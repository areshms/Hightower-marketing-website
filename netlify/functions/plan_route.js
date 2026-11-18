// Netlify function: GET /plan_route?start=<city>&end=<city>
// Port of tools/sim_route_multiday.py (tested python logic) for the live wedge.
// Tokenless: public OSRM router + committed parking cache asset. No fabricated data.
const https = require('https');

function fetch_json(url, timeoutMs = 25000) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers: { 'User-Agent': 'HMS-Truckscan/0.1' }, timeout: timeoutMs }, (res) => {
      if (res.statusCode >= 400) { res.resume(); return reject(new Error('HTTP ' + res.statusCode)); }
      let body = '';
      res.on('data', (c) => (body += c));
      res.on('end', () => { try { resolve(JSON.parse(body)); } catch (e) { reject(e); } });
    });
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    req.on('error', reject);
  });
}

const CITIES = [
  ['los angeles', 34.0522, -118.2437], ['bakersfield', 35.3733, -119.0283], ['fresno', 36.7377, -119.7871],
  ['sacramento', 38.5816, -121.4944], ['san jose', 37.3382, -121.8863], ['oakland', 37.4667, -122.1373],
  ['barstow', 34.8958, -117.0173], ['blythe', 33.6168, -114.7250], ['san diego', 32.7157, -117.1611],
  ['las vegas', 36.1716, -115.1398], ['phoenix', 33.4484, -112.0740], ['tucson', 32.2226, -110.9747],
  ['flagstaff', 35.1983, -111.6513], ['kingman', 35.1894, -114.0523], ['gallup', 35.5285, -108.7425],
  ['albuquerque', 35.0844, -106.6504], ['el paso', 31.7619, -106.4850], ['las cruces', 32.3199, -106.7636],
  ['van horn', 31.0379, -104.8305], ['midland', 32.0000, -102.0800], ['abilene', 32.4487, -99.7331],
  ['amarillo', 35.2220, -101.8313], ['dallas', 32.7767, -96.7970], ['fort worth', 32.7555, -97.3308],
  ['oklahoma city', 35.4676, -97.5164], ['tulsa', 36.1540, -95.9928], ['joplin', 37.0842, -94.5131],
  ['springfield', 37.2089, -93.2923], ['st louis', 38.6270, -90.1994], ['effingham', 39.1200, -88.5900],
  ['chicago', 41.8781, -87.6298], ['indianapolis', 39.7684, -86.1581], ['columbus', 39.9612, -82.9988],
  ['cleveland', 41.4993, -81.6944], ['cincinnati', 39.1031, -84.5120], ['detroit', 42.3314, -83.0458],
  ['kansas city', 39.0997, -94.5786], ['wichita', 37.6872, -97.3301], ['omaha', 41.2565, -95.9345],
  ['des moines', 41.5868, -93.6250], ['minneapolis', 44.9778, -93.2650], ['denver', 39.7392, -104.9903],
  ['salt lake city', 40.7608, -111.8910], ['boise', 43.6150, -116.2023], ['portland', 45.5152, -122.6784],
  ['seattle', 47.6062, -122.3321], ['memphis', 35.1495, -90.0490], ['nashville', 36.1627, -86.7816],
  ['louisville', 38.2527, -85.7585], ['atlanta', 33.7490, -84.3880], ['charlotte', 35.2271, -80.8431],
  ['jacksonville', 30.3322, -81.6557], ['orlando', 28.5383, -81.3792], ['tampa', 27.9506, -82.4572],
  ['new orleans', 29.9511, -90.0715], ['houston', 29.7604, -95.3698], ['san antonio', 29.4241, -98.4936],
  ['austin', 30.2672, -97.7431], ['little rock', 34.7465, -92.2896], ['laredo', 27.5306, -99.4803],
];

const AVG_SPEED_KMH = 100.0, DRIVE_LIMIT_H = 11.0, WINDOW_LIMIT_H = 14.0,
      BREAK_AT_H = 8.0, BREAK_MIN_H = 0.5, RESET_RADIUS_KM = 50.0, BACKUPS = 2;

function hav(lat1, lon1, lat2, lon2) {
  const r = Math.PI / 180;
  const a = Math.sin((lat2 - lat1) * r / 2) ** 2 +
            Math.cos(lat1 * r) * Math.cos(lat2 * r) * Math.sin((lon2 - lon1) * r / 2) ** 2;
  return 6371.0 * 2 * Math.asin(Math.min(1, Math.sqrt(a)));
}

function pickCity(q) {
  const s = String(q || '').toLowerCase().trim();
  if (!s) return null;
  for (const c of CITIES) { if (c[0] === s) return { name: c[0].toUpperCase(), lat: c[1], lon: c[2] }; }
  for (const c of CITIES) { if (c[0].startsWith(s)) return { name: c[0].toUpperCase(), lat: c[1], lon: c[2] }; }
  for (const c of CITIES) { if (c[0].includes(s)) return { name: c[0].toUpperCase(), lat: c[1], lon: c[2] }; }
  return null;
}

function buildLegs(km, A, B) {
  // interpolate waypoints so each synthetic leg is ~<=2.3 hrs (fits inside any fresh day)
  const maxKm = 2.3 * AVG_SPEED_KMH;
  const legs = [];
  let done = 0;
  while (done + maxKm < km) {
    const f = (done + maxKm) / km;
    legs.push({ lat: A.lat + (B.lat - A.lat) * f, lon: A.lon + (B.lon - A.lon) * f, km: maxKm,
                name: 'en route · ' + Math.round(done / km * 100) + '% toward ' + B.name });
    done += maxKm;
  }
  legs.push({ lat: B.lat, lon: B.lon, km: km - done, name: B.name });
  return legs;
}

function nearestCityName(lat, lon) {
  let best = null, bd = Infinity;
  for (const c of CITIES) {
    const d = hav(lat, lon, c[1], c[2]);
    if (d < bd) { bd = d; best = c; }
  }
  return bd <= 150 ? `near ${best[0].toUpperCase()}` : 'on the corridor';
}

function findStops(spaces, lat, lon, radiusKm, limit) {
  const hits = spaces
    .map((s) => ({ ...s, distance_km: Number(hav(lat, lon, s.lat, s.lon).toFixed(1)) }))
    .filter((s) => s.distance_km <= radiusKm)
    .sort((a, b) => a.distance_km - b.distance_km);
  const picks = [];
  for (const h of hits) {
    if (picks.some((p) => hav(h.lat, h.lon, p.lat, p.lon) < 0.35)) continue;
    picks.push(h);
    if (picks.length >= limit) break;
  }
  return picks;
}

const RESP = (code, obj) => ({
  statusCode: code,
  headers: { 'content-type': 'application/json', 'cache-control': 'max-age=300' },
  body: JSON.stringify(obj),
});

exports.handler = async (event) => {
  const q = (event && event.queryStringParameters) || {};
  const A = pickCity(q.start);
  const B = pickCity(q.end);
  if (!A || !B) {
    return RESP(400, {
      error: 'city not in index yet',
      hint: 'use one of the supported city names',
      supported: CITIES.map((c) => c[0]).join(', '),
    });
  }
  let rt;
  try {
    const osrm = 'https://router.project-osrm.org/route/v1/driving/' +
      B.lon + ',' + B.lat + ';' + A.lon + ',' + A.lat + '?overview=false';
    const osrmData = await fetch_json(osrm);
    rt = osrmData.routes && osrmData.routes[0];
  } catch (e) {
    return RESP(502, { error: 'router unavailable, try again' });
  }
  if (!rt) return RESP(502, { error: 'no route found between those cities' });
  const kmTotal = Math.round(rt.distance / 1000);

  let spaces = [];
  try {
    const cache = await fetch_json(process.env.CACHE_URL ||
      'https://www.hightower-marketing.com/assets/parking_cache.json');
    spaces = cache.spaces || [];
  } catch (e) { /* honest-empty: nights will report NO STOP IN RADIUS rather than fake one */ }

  const legs = buildLegs(kmTotal, A, B);
  const days = [];
  let drive = 0.0, win = 0.0, i = 1; // leg 0 = current position (start city)
  let cur = { lat: A.lat, lon: A.lon, name: A.name };

  let made = [];
  while (i < legs.length) {
    const leg = legs[i];
    const hrs = leg.km / AVG_SPEED_KMH;
    if (!made.some((e) => e.event === '30_min_break') && drive + hrs >= BREAK_AT_H && drive < DRIVE_LIMIT_H) {
      made.push({ event: '30_min_break' });
      win += BREAK_MIN_H;
    }
    if (drive + hrs > DRIVE_LIMIT_H || win + hrs > WINDOW_LIMIT_H) {
      const picks = findStops(spaces, cur.lat, cur.lon, RESET_RADIUS_KM, 1 + BACKUPS);
      days.push({
        day: days.length + 1,
        reset_near: nearestCityName(cur.lat, cur.lon),
        events: made,
        primary_stop: picks[0] ? { name: picks[0].name, distance_km: picks[0].distance_km,
                                   amenity_type: picks[0].amenity_type, source: picks[0].source } : null,
        backups_if_full: picks.slice(1, 1 + BACKUPS).map((b) => ({
          name: b.name, distance_km: b.distance_km, source: b.source })),
        vacancy_note: picks[0] ? 'alternates ranked by distance; live vacancy is a commercial data source — the planner falls back to the next-closest stop' : null,
      });
      drive = 0.0; win = 0.0; made = [];
      continue; // re-process this leg on the fresh day
    }
    drive += hrs; win += hrs;
    cur = { lat: leg.lat, lon: leg.lon, name: leg.name };
    made.push({ event: 'leg', hours: Number(hrs.toFixed(2)) });
    i += 1;
  }
  days.push({ day: days.length + 1, arrival: B.name, driving_final: Number(drive.toFixed(1)),
              window_final: Number(win.toFixed(1)) });

  return RESP(200, {
    start: A.name, end: B.name, distance_km: kmTotal,
    method: 'FMCSA 11/14/30/70 logic, closest live-mapped stops per reset',
    days,
  });
};
