// Browser smoke test: signs in as the demo patient and the demo doctor and clicks through the main pages
// in headless Chrome, failing on any page error, uncaught JS exception or missing content.
//
//   python manage.py seed_demo && python manage.py runserver   # in another terminal
//   node tests/smoke.mjs
//
// Env: BASE_URL (default http://127.0.0.1:8000), CHROME (path to Chrome/Chromium). No npm packages needed (Node 22+).
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const BASE = (process.env.BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const CHROME = process.env.CHROME || (process.platform === 'darwin'
  ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' : 'google-chrome');
const PATIENT = { email: 'demo@revivecare.com', password: 'demo1234' };
const DOCTOR = { username: 'doctor', password: 'Doctor-demo-2026' };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const profile = mkdtempSync(join(tmpdir(), 'smoke-'));
const port = 9300 + Math.floor(Math.random() * 600);
const chrome = spawn(CHROME, ['--headless=new', '--no-sandbox', `--remote-debugging-port=${port}`, '--window-size=1280,900',
  `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });

let ws, nextId = 0;
const pending = {}, errors = [], failures = [];
let lastStatus = 0;
const send = (method, params = {}) => new Promise((resolve) => { pending[++nextId] = resolve; ws.send(JSON.stringify({ id: nextId, method, params })); });
const evaluate = async (expression) => {
  const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (r.result?.exceptionDetails) throw new Error(r.result.exceptionDetails.exception?.description || 'evaluate failed');
  return r.result?.result?.value;
};
const waitFor = async (expression, ms = 8000) => {
  for (const end = Date.now() + ms; Date.now() < end; await sleep(150)) {
    if (await evaluate(expression).catch(() => false)) return true;
  }
  return false;
};
async function open(path, mustContain) {
  lastStatus = 0;
  await send('Page.navigate', { url: BASE + path });
  await waitFor(`document.readyState === 'complete'`);
  await sleep(400);
  const text = await evaluate('document.body.textContent');  // textContent: innerText applies CSS uppercase
  const problem = lastStatus !== 200 ? `returned ${lastStatus}` : mustContain && !text.includes(mustContain) ? `is missing "${mustContain}"` : '';
  check(!problem, path, problem);
}
function check(ok, label, why = '') {
  if (!ok) failures.push(`${label} ${why}`.trim());
  console.log(`${ok ? '  ok ' : 'FAIL '} ${label}`);
}

try {
  let target;
  for (let i = 0; i < 40 && !target; i++) {
    await sleep(250);
    target = await fetch(`http://127.0.0.1:${port}/json`).then((r) => r.json()).then((t) => t.find((x) => x.type === 'page')).catch(() => null);
  }
  if (!target) throw new Error(`Chrome did not start (CHROME=${CHROME})`);
  ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));
  ws.onmessage = ({ data }) => {
    const msg = JSON.parse(data);
    if (pending[msg.id]) { pending[msg.id](msg); delete pending[msg.id]; }
    if (msg.method === 'Runtime.exceptionThrown') errors.push(msg.params.exceptionDetails.exception?.description || msg.params.exceptionDetails.text);
    if (msg.method === 'Network.responseReceived' && msg.params.type === 'Document') lastStatus = msg.params.response.status;
  };
  await send('Runtime.enable');
  await send('Network.enable');
  await send('Page.enable');

  console.log('Public pages');
  await open('/', 'ReViveCare');
  await open('/privacy/', 'Privacy Policy');

  console.log('Patient');
  await open('/patient/login/', 'Patient Login');
  await evaluate(`(() => { const f = document.getElementById('login-form') || document.querySelector('form');
    f.email.value = ${JSON.stringify(PATIENT.email)}; f.password.value = ${JSON.stringify(PATIENT.password)};
    document.getElementById('login-btn').click(); })()`);
  check(await waitFor(`location.pathname === '/patient/dashboard/'`), 'patient signs in');
  await open('/patient/dashboard/', 'Welcome back');
  await open('/patient/exercises/', 'Exercise');
  await open('/patient/diary/', 'Pain diary');
  await evaluate(`(() => { document.querySelector('input[name=pain][value="3"]').click(); document.getElementById('diary-notes').value = 'smoke test';
    document.querySelector('main form, form[method=post]:not([action])').requestSubmit(); })()`);
  check(await waitFor(`document.body.textContent.includes('smoke test')`), 'diary entry saves');
  await open('/patient/vitals/', 'Vitals');
  await open('/patient/messages/', 'Messages');
  await open('/patient/history/');
  await open('/patient/chat/');
  await open('/patient/notifications/', 'Notifications');
  await evaluate(`patientLogout()`);
  check(await waitFor(`location.pathname === '/patient/login/'`), 'patient signs out');

  console.log('Doctor');
  await open('/doctor/login/');
  await evaluate(`(() => { document.getElementById('id_username').value = ${JSON.stringify(DOCTOR.username)};
    document.getElementById('id_password').value = ${JSON.stringify(DOCTOR.password)};
    document.getElementById('id_password').form.submit(); })()`);
  check(await waitFor(`location.pathname === '/doctor/'`), 'doctor signs in');
  await open('/doctor/', 'Demo Patient');
  const detail = await evaluate(`[...document.querySelectorAll('a[href^="/doctor/patients/"]')].map((a) => a.getAttribute('href')).find((h) => /^\\/doctor\\/patients\\/\\d+\\/$/.test(h))`);
  check(Boolean(detail), 'patient list links to a patient');
  if (detail) {
    await open(detail, 'Demo Patient');
    check(await waitFor(`document.querySelectorAll('.viz-root svg').length > 0`), 'patient charts render');
    await open(detail + 'report/', 'Progress report');
  }
  await open('/doctor/calendar/');
  await open('/doctor/inbox/');
  await open('/doctor/alerts/');

  check(errors.length === 0, 'no uncaught JS errors', errors.join(' | '));
} catch (err) {
  failures.push(err.message);
  console.error('FAIL', err.message);
} finally {
  ws?.close();
  chrome.kill();
  await sleep(300);
  rmSync(profile, { recursive: true, force: true });
}

console.log(failures.length ? `\n${failures.length} failure(s):\n- ${failures.join('\n- ')}` : '\nAll smoke checks passed.');
process.exit(failures.length ? 1 : 0);
