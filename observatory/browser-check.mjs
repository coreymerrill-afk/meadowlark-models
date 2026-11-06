import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const port = 8765;
const debugPort = 9333;
mkdirSync('/opt/cursor/artifacts', { recursive: true });
const server = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], {
  cwd: fileURLToPath(new URL('..', import.meta.url)),
  stdio: 'ignore'
});
const chrome = spawn('google-chrome', [
  '--headless=new',
  '--no-sandbox',
  '--disable-gpu',
  '--remote-debugging-port=' + debugPort,
  '--user-data-dir=/tmp/obs-chrome',
  '--window-size=1280,1200',
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
  const events = [];
  ws.addEventListener('message', (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const { resolve, reject } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) reject(new Error(JSON.stringify(message.error)));
      else resolve(message.result);
    } else if (message.method) events.push(message);
  });
  return {
    events,
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
    await sleep(250);
    const result = await client.send('Runtime.evaluate', {
      expression: `window.__observatory && window.__observatory.booted ? ({
        booted: true,
        triangles: window.__observatory.triangles,
        errors: window.__observatory.errors,
        claim: document.getElementById('claim').textContent,
        canvas: !!document.querySelector('#view canvas'),
        hinge: window.__observatory.hinge()
      }) : ({booted:false, errors: (window.__observatory && window.__observatory.errors) || []})`,
      returnByValue: true
    });
    sample = result.result.value;
    if (sample && sample.booted) break;
  }
  await client.send('Runtime.evaluate', {
    expression: "document.getElementById('view').scrollIntoView({block:'center'})"
  });
  await sleep(150);
  const shot = await client.send('Page.captureScreenshot', { format: 'png' });
  const failures = client.events.filter((event) => {
    if (event.method === 'Runtime.exceptionThrown') return true;
    if (event.method === 'Network.responseReceived' && event.params.response.status >= 400) return true;
    if (event.method === 'Runtime.consoleAPICalled' && event.params.type === 'error') return true;
    return false;
  });
  ws.close();
  return { sample, png: shot.data, failures };
}

try {
  await sleep(300);
  const desktop = await open('http://127.0.0.1:' + port + '/observatory/', 1280, 1200);
  writeFileSync('/opt/cursor/artifacts/observatory_desktop_view.png', Buffer.from(desktop.png, 'base64'));
  const mobile = await open('http://127.0.0.1:' + port + '/observatory/', 390, 844);
  writeFileSync('/opt/cursor/artifacts/observatory_mobile_view.png', Buffer.from(mobile.png, 'base64'));
  const home = await fetch('http://127.0.0.1:' + port + '/').then((r) => r.text());
  const links = [
    '/observatory/manifest.json',
    '/observatory/stl/fit_coupon.stl',
    '/observatory/h3c_celestial_observatory_stls.zip',
    '/observatory/h3c_celestial_observatory.3mf',
    '/observatory/generate_observatory.py',
    '/observatory/renders/preview.png',
    '/dollhouse/vendor/three.min.js'
  ];
  const statuses = {};
  for (const link of links) {
    statuses[link] = (await fetch('http://127.0.0.1:' + port + link)).status;
  }
  const report = {
    desktop: { sample: desktop.sample, failures: desktop.failures.length },
    mobile: { sample: mobile.sample, failures: mobile.failures.length },
    homeLinksObservatory: home.includes('href="/observatory/"'),
    statuses
  };
  console.log(JSON.stringify(report, null, 2));
  const bad = Object.values(statuses).some((code) => code !== 200)
    || !desktop.sample.booted
    || !mobile.sample.booted
    || desktop.sample.triangles < 1000
    || desktop.failures.length
    || mobile.failures.length
    || !home.includes('href="/observatory/"');
  if (bad) process.exitCode = 1;
} finally {
  chrome.kill('SIGKILL');
  server.kill('SIGKILL');
}
