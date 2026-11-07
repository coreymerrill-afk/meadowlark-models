import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { get as httpGet } from 'node:http';
import { fileURLToPath } from 'node:url';

function getStatus(url) {
  return new Promise((resolve) => {
    const req = httpGet(url, (response) => {
      response.resume();
      resolve(response.statusCode);
    });
    req.on('error', (error) => resolve(String(error)));
  });
}

const port = 8771;
const debugPort = 9341;
mkdirSync('/opt/cursor/artifacts', { recursive: true });
const server = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], {
  cwd: fileURLToPath(new URL('../..', import.meta.url)),
  stdio: 'ignore'
});
const chrome = spawn('google-chrome', [
  '--headless=new',
  '--no-sandbox',
  '--disable-gpu',
  '--remote-debugging-port=' + debugPort,
  '--user-data-dir=/tmp/qa-chrome',
  '--window-size=1280,900',
  'about:blank'
], { stdio: 'ignore' });

function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

async function debugTarget() {
  for (let i = 0; i < 40; i++) {
    try {
      const list = await fetch('http://127.0.0.1:' + debugPort + '/json/list').then((r) => r.json());
      const page = list.find((item) => item.type === 'page' && item.webSocketDebuggerUrl);
      if (page) return page;
    } catch { /* chrome still starting */ }
    await sleep(150);
  }
  throw new Error('Chrome debug port did not open');
}

function cdp(ws) {
  let seq = 0;
  const pending = new Map();
  ws.addEventListener('message', (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const { resolve, reject } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) reject(new Error(JSON.stringify(message.error)));
      else resolve(message.result);
    }
  });
  return {
    send(method, params = {}) {
      const id = ++seq;
      ws.send(JSON.stringify({ id, method, params }));
      return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
    }
  };
}

async function open(url, width, height) {
  const target = await debugTarget();
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve);
    ws.addEventListener('error', reject);
  });
  const client = cdp(ws);
  await client.send('Page.enable');
  await client.send('Runtime.enable');
  await client.send('Network.enable');
  await client.send('Emulation.setDeviceMetricsOverride', {
    width, height, deviceScaleFactor: 1, mobile: width < 500
  });
  await client.send('Page.navigate', { url });
  const started = Date.now();
  let sample = null;
  while (Date.now() - started < 20000) {
    await sleep(200);
    const result = await client.send('Runtime.evaluate', {
      expression: `window.__queenAnne && window.__queenAnne.booted ? ({
        booted: true,
        triangles: window.__queenAnne.triangles,
        instances: window.__queenAnne.entries.length,
        mode: window.__queenAnne.mode,
        errors: window.__queenAnne.errors,
        claim: document.getElementById('claim').textContent,
        buttons: [...document.querySelectorAll('.modes button')].map((b) => b.getAttribute('data-mode'))
      }) : ({ booted: false, errors: (window.__queenAnne && window.__queenAnne.errors) || [], claim: document.getElementById('claim') && document.getElementById('claim').textContent })`,
      returnByValue: true
    });
    sample = result.result.value;
    if (sample && sample.booted) break;
  }
  return { client, ws, sample };
}

async function shot(client, mode, file) {
  await client.send('Runtime.evaluate', {
    expression: `document.querySelector('.modes button[data-mode="${mode}"]').click(); document.getElementById('view').scrollIntoView({block:'center'});`
  });
  await sleep(500);
  const read = await client.send('Runtime.evaluate', {
    expression: `({
      mode: window.__queenAnne.mode,
      visible: window.__queenAnne.entries.filter((e) => e.mesh.visible).length,
      copy: document.getElementById('mode-copy').textContent
    })`,
    returnByValue: true
  });
  const image = await client.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(file, Buffer.from(image.data, 'base64'));
  return read.result.value;
}

const desktop = await open('http://127.0.0.1:' + port + '/dollhouse/queen-anne/', 1280, 900);
const closed = await shot(desktop.client, 'closed', '/opt/cursor/artifacts/queen-anne-closed-desktop.png');
const opened = await shot(desktop.client, 'open', '/opt/cursor/artifacts/queen-anne-open-desktop.png');
const stairs = await shot(desktop.client, 'stairs', '/opt/cursor/artifacts/queen-anne-stairs-desktop.png');
const attachment = await shot(desktop.client, 'attachment', '/opt/cursor/artifacts/queen-anne-attachment-desktop.png');
await desktop.client.send('Runtime.evaluate', {
  expression: `document.getElementById('plan-card').scrollIntoView({block:'start'})`
});
await sleep(400);
const planBox = await desktop.client.send('Runtime.evaluate', {
  expression: `(() => { const node = document.getElementById('plan-svg'); const svg = node.querySelector('svg'); const rect = node.getBoundingClientRect(); return {x: Math.max(0, rect.x), y: Math.max(0, rect.y), width: Math.max(1, rect.width), height: Math.max(1, Math.min(rect.height, 640)), scale: 1, children: node.childElementCount, svgChildren: svg ? svg.childElementCount : 0, sample: svg ? svg.innerHTML.slice(0, 180) : '', top: rect.top}; })()`,
  returnByValue: true
});
const planClip = { x: planBox.result.value.x, y: planBox.result.value.y, width: planBox.result.value.width, height: planBox.result.value.height, scale: 1 };
const full = await desktop.client.send('Page.captureScreenshot', { format: 'png' });
writeFileSync('/opt/cursor/artifacts/queen-anne-floorplan-full.png', Buffer.from(full.data, 'base64'));
const lighting = await shot(desktop.client, 'lighting', '/opt/cursor/artifacts/queen-anne-lighting-desktop.png');
desktop.ws.close();

const mobile = await open('http://127.0.0.1:' + port + '/dollhouse/queen-anne/', 390, 844);
const mobileClosed = await shot(mobile.client, 'closed', '/opt/cursor/artifacts/queen-anne-closed-mobile.png');
const mobileOpen = await shot(mobile.client, 'open', '/opt/cursor/artifacts/queen-anne-open-mobile.png');
mobile.ws.close();

const links = [
  '/dollhouse/queen-anne/',
  '/dollhouse/queen-anne/manifest.json',
  '/dollhouse/queen-anne/stl/qa4_roof_turret_v4.stl',
  '/dollhouse/queen-anne/stl/qa4_facade_front_l1_v4.stl',
  '/dollhouse/queen-anne/stl/qa4_stair_lower_v4.stl',
  '/dollhouse/queen-anne/concept/approved-direction.jpg',
  '/dollhouse/',
  '/marble-factory/',
  '/marble-system/',
  '/observatory/',
  '/'
];
const statuses = {};
for (const link of links) statuses[link] = await getStatus('http://127.0.0.1:' + port + link);

const home = await new Promise((resolve, reject) => {
  httpGet('http://127.0.0.1:' + port + '/', (response) => {
    let body = '';
    response.setEncoding('utf8');
    response.on('data', (chunk) => { body += chunk; });
    response.on('end', () => resolve(body));
  }).on('error', reject);
});
const kept = ['/dollhouse/', '/dollhouse/queen-anne/', '/marble-factory/', '/marble-system/', '/observatory/']
  .every((href) => home.includes('href="' + href + '"'));

const report = { desktop: desktop.sample, closed, opened, stairs, attachment, mobile: mobile.sample, mobileClosed, mobileOpen, statuses, kept };
console.log(JSON.stringify(report, null, 2));
const badStatus = Object.entries(statuses).filter(([, code]) => code !== 200);
const failed = !desktop.sample.booted || desktop.sample.errors.length || badStatus.length || !kept
  || closed.mode !== 'closed' || opened.mode !== 'open' || stairs.mode !== 'stairs' || attachment.mode !== 'attachment'
  || mobileClosed.mode !== 'closed' || mobileOpen.mode !== 'open';
server.kill();
chrome.kill();
process.exit(failed ? 1 : 0);
