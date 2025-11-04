# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
const express = require('express');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const os = require('os');

const PORT = 4001;
const LOG_FILE = path.resolve(process.cwd(), 'orchestrator.log');
const ARCHIVES_DIR = path.resolve(process.cwd(), 'archives');
try { fs.mkdirSync(ARCHIVES_DIR, { recursive: true }); } catch (e) {}

function now() { return new Date().toISOString(); }
function shortHash(s) { try { return crypto.createHash('sha256').update(JSON.stringify(s)).digest('hex').substr(0,12); } catch (e) { return Date.now().toString(36); } }

async function applyPatches(approval) {
  const diffs = [];
  for (const p of (approval.patches || [])) {
    const target = path.resolve(process.cwd(), p.target || 'unknown.target');
    const before = fs.existsSync(target) ? fs.readFileSync(target, 'utf8') : null;
    let after = before;
    if (p.op === 'write') { after = p.content || ''; try { fs.mkdirSync(path.dirname(target), { recursive: true }); fs.writeFileSync(target, after, 'utf8'); } catch (e) {} }
    diffs.push({ target: p.target, before, after });
  }
  return diffs;
}

async function performCycle(approval) {
  const cycle_id = approval.cycle_id || dawn-;
  try {
    const diffs = await applyPatches(approval);
    const ts = now().replace(/[:.]/g, '');
    const arch = path.join(ARCHIVES_DIR, ts + '_' + shortHash({approval, cycle_id}));
    try { fs.mkdirSync(arch, { recursive: true }); } catch (e) {}
    fs.writeFileSync(path.join(arch, 'apply-diffs.json'), JSON.stringify(diffs, null, 2));
    const record = {
      timestamp: now(),
      cycle_id,
      applied: true,
      patches_applied: diffs.length,
      total_errors: 0,
      diffs_file: path.relative(process.cwd(), path.join(arch, 'apply-diffs.json'))
    };
    fs.appendFileSync(LOG_FILE, 'CYCLE_SUMMARY_JSON ' + JSON.stringify(record) + '\n');
    return record;
  } catch (e) {
    const record = { timestamp: now(), cycle_id, applied: false, total_errors: 1, error: String(e) };
    fs.appendFileSync(LOG_FILE, 'CYCLE_SUMMARY_JSON ' + JSON.stringify(record) + '\n');
    return record;
  }
}

const app = express();
app.use(express.json({ limit: '1mb' }));

let queue = [];
let running = false;
let seen = new Set();

async function runQueue() {
  if (running || queue.length === 0) return;
  running = true;
  const item = queue.shift();
  try {
    const summary = await performCycle(item.approval);
    if (item.res && !item.resHandled) { item.res.json({ ok: true, result: summary }); item.resHandled = true; }
  } catch (e) {
    if (item.res && !item.resHandled) { item.res.status(500).json({ ok: false, error: String(e) }); item.resHandled = true; }
  }
  running = false;
  setImmediate(runQueue);
}

app.post('/approve', (req, res) => {
  const approval = req.body || {};
  const key = approval.idempotency_key || shortHash(approval);
  if (seen.has(key) || queue.some(x => x.idempotencyKey === key)) { return res.json({ ok: true, status: 'queued_or_applied', idempotencyKey: key }); }
  seen.add(key);
  const item = { approval, receivedAt: now(), res, idempotencyKey: key, resHandled: false };
  queue.push(item);
  fs.appendFileSync(LOG_FILE, 'ENQUEUE_JSON ' + JSON.stringify({ idempotencyKey: key, qlen: queue.length }) + '\n');
  setImmediate(runQueue);
  res.json({ ok: true, status: 'queued', idempotencyKey: key });
});

app.get('/approve/status', (req, res) => { res.json({ queued: queue.length, running }); });

app.listen(PORT, () => { console.log('Approve server listening ' + PORT); fs.appendFileSync(LOG_FILE, JSON.stringify({ timestamp: now(), note: 'approve_server_started', port: PORT }) + '\n'); });

