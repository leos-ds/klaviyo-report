const http = require('http');
const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');
const PORT = process.env.PORT || 9876;
const dir = __dirname;
const ROOT = path.resolve(dir, '..');

// Load .env for CLICKUP_TOKEN
function loadEnv() {
  const envPath = path.join(ROOT, '.env');
  const env = {};
  try {
    fs.readFileSync(envPath, 'utf8').split('\n').forEach(line => {
      const m = line.match(/^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$/);
      if (m) env[m[1]] = m[2].replace(/^["']|["']$/g, '').trim();
    });
  } catch (e) {}
  return env;
}

function jsonResp(res, code, obj) {
  res.writeHead(code, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
  res.end(JSON.stringify(obj));
}

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', d => { body += d; });
    req.on('end', () => {
      try { resolve(JSON.parse(body || '{}')); }
      catch (e) { resolve({}); }
    });
    req.on('error', reject);
  });
}

// ── ClickUp helpers ──────────────────────────────────────────────────────────

const CLICKUP_LIST_ID = '901515412227';

async function cuFetch(token, path, opts = {}) {
  const { default: fetch } = await import('node-fetch').catch(() => null)
    || await import('undici').then(m => ({ default: m.fetch })).catch(() => null)
    || { default: global.fetch };
  if (!fetch) throw new Error('No fetch implementation available');
  const res = await fetch(`https://api.clickup.com/api/v2${path}`, {
    headers: { Authorization: token, 'Content-Type': 'application/json' },
    ...opts,
  });
  return res.json();
}

async function cuFetchNative(token, cuPath, opts = {}) {
  return new Promise((resolve, reject) => {
    const https = require('https');
    const url = new URL(`https://api.clickup.com/api/v2${cuPath}`);
    const reqOpts = {
      hostname: url.hostname,
      path: url.pathname + url.search,
      method: opts.method || 'GET',
      headers: {
        Authorization: token,
        'Content-Type': 'application/json',
        ...(opts.headers || {}),
      },
    };
    const req = https.request(reqOpts, (res) => {
      let data = '';
      res.on('data', d => { data += d; });
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { resolve({ error: data }); }
      });
    });
    req.on('error', reject);
    if (opts.body) req.write(opts.body);
    req.end();
  });
}

async function getExistingTasks(token, page = 0) {
  const data = await cuFetchNative(token,
    `/list/${CLICKUP_LIST_ID}/task?page=${page}&include_closed=true`
  );
  return data.tasks || [];
}

async function getAllExistingTasks(token) {
  const all = [];
  let page = 0;
  while (true) {
    const tasks = await getExistingTasks(token, page);
    all.push(...tasks);
    if (tasks.length < 100) break;
    page++;
  }
  return all;
}

async function createTask(token, title, description, tags) {
  return cuFetchNative(token, `/list/${CLICKUP_LIST_ID}/task`, {
    method: 'POST',
    body: JSON.stringify({
      name: title,
      description: description || '',
      tags: tags || [],
      status: 'to do',
    }),
  });
}

// ── HTTP server ──────────────────────────────────────────────────────────────

http.createServer(async (req, res) => {
  // CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,POST', 'Access-Control-Allow-Headers': 'Content-Type' });
    res.end();
    return;
  }

  const url = new URL(req.url, `http://localhost:${PORT}`);

  // ── GET /api/refresh ──────────────────────────────────────────────────────
  if (url.pathname === '/api/refresh' && req.method === 'GET') {
    const python = process.env.PYTHON || 'python3';
    const script = path.join(ROOT, 'scripts', 'generate_report.py');
    const timeframe = url.searchParams.get('timeframe') || 'last_90_days';
    const args = [script, '--timeframe', timeframe];
    execFile(python, args, { cwd: ROOT, timeout: 300000 }, (err, stdout, stderr) => {
      if (err) {
        console.error('Refresh error:', stderr);
        jsonResp(res, 500, { ok: false, error: stderr.slice(-500) });
      } else {
        console.log('Report refreshed:', stdout.slice(-200));
        jsonResp(res, 200, { ok: true, message: 'Report regenerated', timeframe });
      }
    });
    return;
  }

  // ── POST /api/sync-clickup ────────────────────────────────────────────────
  if (url.pathname === '/api/sync-clickup' && req.method === 'POST') {
    const env = loadEnv();
    const token = env.CLICKUP_API_TOKEN || env.CLICKUP_TOKEN || process.env.CLICKUP_API_TOKEN || process.env.CLICKUP_TOKEN;
    if (!token) {
      jsonResp(res, 400, { ok: false, error: 'CLICKUP_TOKEN not set in .env' });
      return;
    }
    try {
      const body = await parseBody(req);
      const tasks = body.tasks || []; // [{title, description, tags}]

      // Fetch all existing tasks once
      const existing = await getAllExistingTasks(token);
      const existingNames = new Set(existing.map(t => t.name.trim().toLowerCase()));

      const results = { created: [], skipped: [] };
      for (const task of tasks) {
        const key = task.title.trim().toLowerCase();
        if (existingNames.has(key)) {
          results.skipped.push(task.title);
        } else {
          await createTask(token, task.title, task.description, task.tags);
          results.created.push(task.title);
          existingNames.add(key); // prevent duplicate within batch
        }
      }
      jsonResp(res, 200, { ok: true, ...results });
    } catch (e) {
      console.error('ClickUp sync error:', e);
      jsonResp(res, 500, { ok: false, error: String(e) });
    }
    return;
  }

  // ── Static files ──────────────────────────────────────────────────────────
  // For root, find the latest report_*.html file
  let staticPath = url.pathname;
  if (staticPath === '/') {
    try {
      const reports = fs.readdirSync(dir).filter(f => f.match(/^report_\d{4}-\d{2}-\d{2}\.html$/)).sort().reverse();
      staticPath = reports.length ? '/' + reports[0] : '/report.html';
    } catch (e) { staticPath = '/report_2026-05-14.html'; }
  }
  const file = path.join(dir, staticPath);
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); res.end('Not found'); return; }
    const ext = path.extname(file);
    const ct = ext === '.html' ? 'text/html; charset=utf-8' :
               ext === '.js'   ? 'application/javascript' :
               ext === '.css'  ? 'text/css' : 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': ct });
    res.end(data);
  });

}).listen(PORT, () => console.log(`Digismoothie report server on :${PORT}`));

// ── Nightly auto-refresh ─────────────────────────────────────────────────────

function scheduleNightlyRefresh() {
  const now = new Date();
  const next = new Date(now);
  next.setHours(2, 0, 0, 0); // 2:00 AM
  if (next <= now) next.setDate(next.getDate() + 1);
  const msUntil = next - now;
  const hoursUntil = (msUntil / 3600000).toFixed(1);
  console.log(`Nightly refresh scheduled in ${hoursUntil}h (at 02:00)`);
  setTimeout(() => {
    runNightlyRefresh();
    setInterval(runNightlyRefresh, 24 * 60 * 60 * 1000);
  }, msUntil);
}

function runNightlyRefresh() {
  const python = process.env.PYTHON || 'python3';
  const script = path.join(ROOT, 'scripts', 'generate_report.py');
  console.log(`[${new Date().toISOString()}] Nightly refresh starting…`);
  execFile(python, [script], { cwd: ROOT, timeout: 300000 }, (err, stdout, stderr) => {
    if (err) {
      console.error(`Nightly refresh failed: ${stderr.slice(-300)}`);
    } else {
      console.log(`Nightly refresh done.`);
    }
  });
}

scheduleNightlyRefresh();
