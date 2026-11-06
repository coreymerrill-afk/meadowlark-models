import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const port = 8771;
const debugPort = 9341;
mkdirSync('/opt/cursor/artifacts', { recursive: true });
const server = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], {
  cwd: fileURLToPath(new URL('..', import.meta.url)),
  stdio: 'ignore'
});
const chrome = spawn('google-chrome', [
  '--headless=new', '--no-sandbox', '--disable-gpu',
  '--remote-debugging-port=' + debugPort,
  '--user-data-dir=/tmp/msys-chrome',
  '--window-size=1280,1400',
  'about:blank'
], { stdio: 'ignore' });

function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

async function debugTarget() {
  for (let i = 0; i < 40; i++) {
    try {
      const list = await fetch('http://127.0.0.1:' + debugPort + '/json/list').then((r) => r.json());
      const page = list.find((item) => item.type === 'page' && item.webSocketDebuggerUrl);
      if (page) return page;
    } catch { /* starting */ }
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

async function evaluate(client, expression) {
  const result = await client.send('Runtime.evaluate', { expression, returnByValue: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
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
  client.events.length = 0;
  await client.send('Page.navigate', { url });
  const started = Date.now();
  let sample = null;
  while (Date.now() - started < 30000) {
    await sleep(250);
    sample = await evaluate(client, `window.__marble2 && window.__marble2.booted ? ({
      booted: true,
      triangles: window.__marble2.triangles,
      errors: window.__marble2.errors,
      loadedParts: window.__marble2.loadedParts,
      layout: window.__marble2.layout,
      claim: document.getElementById('claim').textContent,
      canvas: !!document.querySelector('#view canvas'),
      error: document.getElementById('error').textContent
    }) : ({booted:false, error: document.getElementById('error') ? document.getElementById('error').textContent : ''})`);
    if (sample && (sample.booted || sample.error)) break;
  }
  return { client, ws, sample };
}

function failuresOf(client) {
  return client.events.filter((event) => {
    if (event.method === 'Runtime.exceptionThrown') return true;
    if (event.method === 'Network.responseReceived' && event.params.response.status >= 400) return true;
    if (event.method === 'Runtime.consoleAPICalled' && event.params.type === 'error') return true;
    return false;
  }).map((event) => {
    if (event.method === 'Network.responseReceived') return event.params.response.status + ' ' + event.params.response.url;
    return event.method;
  });
}

try {
  await sleep(300);
  const desktop = await open('http://127.0.0.1:' + port + '/marble-system/', 1280, 1400);
  if (!desktop.sample || !desktop.sample.booted) {
    console.log(JSON.stringify({ sample: desktop.sample, failures: failuresOf(desktop.client) }, null, 2));
    throw new Error('page did not boot');
  }
  const motion = await evaluate(desktop.client, `(() => {
    const before = window.__marble2.sample('v1-lift_crank-0', [0,0,0,1]);
    const track = window.__marble2.sample('S160_1', [0,0,0,1]);
    window.__marble2.setCrank(90);
    const after = window.__marble2.sample('v1-lift_crank-0', [0,0,0,1]);
    const trackAfter = window.__marble2.sample('S160_1', [0,0,0,1]);
    const h = window.__marble2.stepHeight('h0', 5);
    const post = window.__marble2.sample('h0-post', [0,0,0,1]);
    document.getElementById('btn-b').click();
    return {
      crankMoved: Math.hypot(after[0]-before[0], after[1]-before[1], after[2]-before[2]),
      trackMoved: Math.hypot(trackAfter[0]-track[0], trackAfter[1]-track[1], trackAfter[2]-track[2]),
      height: h,
      postZ: post[2],
      layout: window.__marble2.layout
    };
  })()`);
  await sleep(400);
  const shotB = await desktop.client.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync('/opt/cursor/artifacts/marble_v2_hold_layout_b.png', Buffer.from(shotB.data, 'base64'));
  await evaluate(desktop.client, `window.__marble2.setLayout('A'); document.getElementById('btn-frame').click();`);
  await sleep(300);
  const shotA = await desktop.client.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync('/opt/cursor/artifacts/marble_v2_hold_banner.png', Buffer.from(shotA.data, 'base64'));
  await evaluate(desktop.client, `document.getElementById('tab-print').click()`);
  await sleep(200);
  const shotP = await desktop.client.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync('/opt/cursor/artifacts/marble_v2_hold_downloads.png', Buffer.from(shotP.data, 'base64'));
  const dom = await evaluate(desktop.client, `({
    hrefs: Array.from(document.querySelectorAll('a')).map((a) => a.getAttribute('href')),
    text: document.getElementById('print-root').innerText,
    rows: document.querySelectorAll('#part-list .part-row').length
  })`);
  const desktopFailures = failuresOf(desktop.client);
  desktop.ws.close();

  const mobile = await open('http://127.0.0.1:' + port + '/marble-system/', 390, 844);
  await sleep(200);
  await evaluate(mobile.client, `document.getElementById('view').scrollIntoView({block:'center'})`);
  await sleep(200);
  const shotM = await mobile.client.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync('/opt/cursor/artifacts/marble_v2_mobile.png', Buffer.from(shotM.data, 'base64'));
  const mobileFailures = failuresOf(mobile.client);
  mobile.ws.close();

  const links = [
    '/marble-system/',
    '/marble-system/kit/manifest.json',
    '/marble-system/scenes.json',
    '/marble-system/stl/fit_coupon.stl',
    '/marble-system/stl/track_S160.stl',
    '/marble-system/stl/track_HX360.stl',
    '/marble-system/stl/sleeve_short.stl',
    '/marble-system/marble-system-v2-kit.zip',
    '/marble-system/kit/marble_system_v2_layoutA.3mf',
    '/marble-system/README.md',
    '/marble-system/RESEARCH_BRIEF.md',
    '/marble-factory/',
    '/marble-factory/stl/lift_housing_back.stl',
    '/observatory/',
    '/dollhouse/',
    '/workbench/'
  ];
  const statuses = {};
  for (const link of links) statuses[link] = (await fetch('http://127.0.0.1:' + port + link)).status;
  const report = {
    desktop: desktop.sample,
    motion,
    dom: {
      rows: dom.rows,
      hasZip: dom.hrefs.includes('/marble-system/marble-system-v2-kit.zip'),
      has3mf: dom.hrefs.includes('/marble-system/kit/marble_system_v2_layoutA.3mf'),
      hasCoupon: dom.hrefs.includes('/marble-system/stl/fit_coupon.stl'),
      held: /Held/.test(dom.text)
    },
    desktopFailures,
    mobile: mobile.sample,
    mobileFailures,
    statuses
  };
  console.log(JSON.stringify(report, null, 2));
  const bad = Object.values(statuses).some((code) => code !== 200)
    || !desktop.sample.booted || !mobile.sample.booted
    || desktop.sample.loadedParts !== 43
    || mobile.sample.loadedParts !== 43
    || desktop.sample.errors.length || mobile.sample.errors.length
    || desktop.sample.error || mobile.sample.error
    || desktopFailures.length || mobileFailures.length
    || motion.crankMoved < 1
    || motion.trackMoved > 1e-4
    || motion.height !== 170
    || motion.layout !== 'B'
    || dom.rows !== 36
    || dom.hrefs.includes('/marble-system/marble-system-v2-kit.zip')
    || dom.hrefs.includes('/marble-system/kit/marble_system_v2_layoutA.3mf')
    || !dom.hrefs.includes('/marble-system/stl/fit_coupon.stl')
    || !/Held/.test(dom.text)
    || !/do not print full kit yet/.test(desktop.sample.claim);
  if (bad) process.exitCode = 1;
} finally {
  chrome.kill('SIGKILL');
  server.kill('SIGKILL');
}
