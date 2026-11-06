import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const port = 8766;
const debugPort = 9334;
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
  '--user-data-dir=/tmp/marble-chrome',
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

async function evaluate(client, expression) {
  const result = await client.send('Runtime.evaluate', { expression, returnByValue: true });
  if (result.exceptionDetails) {
    throw new Error(JSON.stringify(result.exceptionDetails));
  }
  return result.result.value;
}

async function open(url, width, height, readyExpression) {
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
    const probe = readyExpression || `window.__marble && window.__marble.booted ? ({
      booted: true,
      triangles: window.__marble.triangles,
      errors: window.__marble.errors,
      loadedParts: window.__marble.loadedParts,
      assemblyCount: window.__marble.assemblyCount,
      crank: window.__marble.crank,
      claim: document.getElementById('claim').textContent,
      canvas: !!document.querySelector('#view canvas'),
      error: document.getElementById('error').textContent
    }) : ({booted:false, errors: (window.__marble && window.__marble.errors) || [], error: document.getElementById('error') ? document.getElementById('error').textContent : ''})`;
    sample = await evaluate(client, probe);
    if (readyExpression ? sample : sample && sample.booted) break;
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
    if (event.method === 'Runtime.consoleAPICalled') {
      return event.params.args.map((arg) => arg.value || arg.description || '').join(' ');
    }
    return event.method;
  });
}

try {
  await sleep(400);
  const desktop = await open('http://127.0.0.1:' + port + '/marble-factory/', 1280, 1400);
  const rested = await desktop.client.send('Runtime.evaluate', {
    expression: `(() => {
      const before = window.__marble.sample('lift_crank', 0, [0,0,0,1]);
      const clip = window.__marble.sample('lift_clip', 0, [0,0,0,1]);
      const pawl = window.__marble.sample('lift_pawl', 0, [0,0,0,1]);
      window.__marble.setCrank(90);
      const after = window.__marble.sample('lift_crank', 0, [0,0,0,1]);
      const clipAfter = window.__marble.sample('lift_clip', 0, [0,0,0,1]);
      const pawlAfter = window.__marble.sample('lift_pawl', 0, [0,0,0,1]);
      const moved = Math.hypot(after[0]-before[0], after[1]-before[1], after[2]-before[2]);
      const clipMoved = Math.hypot(clipAfter[0]-clip[0], clipAfter[1]-clip[1], clipAfter[2]-clip[2]);
      const pawlMoved = Math.hypot(pawlAfter[0]-pawl[0], pawlAfter[1]-pawl[1], pawlAfter[2]-pawl[2]);
      document.getElementById('btn-front').click();
      return { moved, clipMoved, pawlMoved, crank: window.__marble.crank };
    })()`,
    returnByValue: true
  });
  await sleep(400);
  await desktop.client.send('Runtime.evaluate', {
    expression: "document.getElementById('view').scrollIntoView({block:'center'})"
  });
  await sleep(200);
  const frontShot = await desktop.client.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync('/opt/cursor/artifacts/marble_desktop_crank.png', Buffer.from(frontShot.data, 'base64'));

  await desktop.client.send('Runtime.evaluate', {
    expression: `(() => {
      window.__marble.setCrank(0);
      document.getElementById('explode').value = '0';
      document.getElementById('explode').dispatchEvent(new Event('input', { bubbles: true }));
      document.getElementById('btn-reset').click();
    })()`
  });
  await sleep(300);
  const assembledShot = await desktop.client.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync('/opt/cursor/artifacts/marble_desktop_assembled.png', Buffer.from(assembledShot.data, 'base64'));

  await desktop.client.send('Runtime.evaluate', {
    expression: `(() => {
      document.getElementById('explode').value = '100';
      document.getElementById('explode').dispatchEvent(new Event('input', { bubbles: true }));
      document.getElementById('btn-reset').click();
    })()`
  });
  await sleep(300);
  const spreadShot = await desktop.client.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync('/opt/cursor/artifacts/marble_desktop_spread.png', Buffer.from(spreadShot.data, 'base64'));

  await desktop.client.send('Runtime.evaluate', {
    expression: `document.getElementById('tab-print').click()`
  });
  await sleep(200);
  const printShot = await desktop.client.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync('/opt/cursor/artifacts/marble_desktop_print.png', Buffer.from(printShot.data, 'base64'));

  const dom = await evaluate(desktop.client, `(() => {
    const hrefs = Array.from(document.querySelectorAll('a')).map((a) => a.getAttribute('href'));
    return {
      parts: document.querySelectorAll('#part-list .part-row').length,
      hrefs,
      claim: document.getElementById('claim').textContent,
      printText: document.getElementById('print-root').innerText
    };
  })()`);
  const desktopFailures = failuresOf(desktop.client);
  desktop.ws.close();

  const mobile = await open('http://127.0.0.1:' + port + '/marble-factory/', 390, 844);
  await sleep(300);
  await mobile.client.send('Runtime.evaluate', {
    expression: "document.getElementById('view').scrollIntoView({block:'center'})"
  });
  await sleep(200);
  const mobileShot = await mobile.client.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync('/opt/cursor/artifacts/marble_mobile_factory.png', Buffer.from(mobileShot.data, 'base64'));
  await mobile.client.send('Runtime.evaluate', {
    expression: `document.getElementById('tab-parts').click()`
  });
  await sleep(200);
  const partsShot = await mobile.client.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync('/opt/cursor/artifacts/marble_mobile_parts.png', Buffer.from(partsShot.data, 'base64'));
  const mobileFailures = failuresOf(mobile.client);
  mobile.ws.close();

  const homePage = await open('http://127.0.0.1:' + port + '/', 1280, 1200, `(() => {
    const card = document.querySelector('a[href="/marble-factory/"]');
    const kept = ['/observatory/','/dollhouse/','/workbench/'].every((href) => document.querySelector('a[href="' + href + '"]'));
    return card ? { ready: true, text: card.innerText, kept } : null;
  })()`);
  await homePage.client.send('Runtime.evaluate', {
    expression: `document.querySelector('a[href="/marble-factory/"]').scrollIntoView({block:'center'})`
  });
  await sleep(200);
  const homeShot = await homePage.client.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync('/opt/cursor/artifacts/marble_homepage_card.png', Buffer.from(homeShot.data, 'base64'));
  const homeCard = homePage.sample;
  homePage.ws.close();

  const home = await fetch('http://127.0.0.1:' + port + '/').then((r) => r.text());
  const links = [
    '/marble-factory/',
    '/marble-factory/manifest.json',
    '/marble-factory/assembly.json',
    '/marble-factory/stl/fit_coupon.stl',
    '/marble-factory/stl/lift_housing_back.stl',
    '/marble-factory/stl/ball_35.stl',
    '/marble-factory/stl/track_switch_Y.stl',
    '/marble-factory/marble-factory-kit.zip',
    '/marble-factory/marble_factory_assembly.3mf',
    '/marble-factory/README.md',
    '/marble-factory/src/export.py',
    '/marble-factory/reports/VALIDATION.md',
    '/marble-factory/slice/SLICE_REPORT.md',
    '/marble-factory/renders/01_overview.png',
    '/observatory/',
    '/dollhouse/',
    '/workbench/',
    '/dollhouse/vendor/three.min.js'
  ];
  const statuses = {};
  for (const link of links) {
    const response = await fetch('http://127.0.0.1:' + port + link);
    statuses[link] = response.status;
  }
  const report = {
    desktop: desktop.sample,
    crank: rested.result.value,
    dom: {
      parts: dom.parts,
      hasZip: dom.hrefs.includes('/marble-factory/marble-factory-kit.zip'),
      has3mf: dom.hrefs.includes('/marble-factory/marble_factory_assembly.3mf'),
      hasCoupon: dom.hrefs.includes('/marble-factory/stl/fit_coupon.stl'),
      claim: dom.claim,
      mentions1715: dom.printText.includes('17.15'),
      mentionsExtras: /not drop-in/i.test(dom.printText)
    },
    desktopFailures,
    mobile: mobile.sample,
    mobileFailures,
    homeHasMarble: home.includes('href="/marble-factory/"'),
    homeHasObservatory: home.includes('href="/observatory/"'),
    homeCard,
    statuses
  };
  console.log(JSON.stringify(report, null, 2));
  const badStatus = Object.entries(statuses).filter((entry) => entry[1] !== 200);
  const bad = badStatus.length
    || !desktop.sample.booted
    || !mobile.sample.booted
    || desktop.sample.loadedParts !== 32
    || mobile.sample.loadedParts !== 32
    || desktop.sample.assemblyCount !== 38
    || desktop.sample.triangles < 100000
    || desktop.sample.errors.length
    || mobile.sample.errors.length
    || desktop.sample.error
    || desktopFailures.length
    || mobileFailures.length
    || rested.result.value.moved < 1
    || rested.result.value.clipMoved > 1e-6
    || rested.result.value.pawlMoved > 1e-6
    || dom.parts !== 32
    || !dom.hrefs.includes('/marble-factory/marble-factory-kit.zip')
    || !home.includes('href="/marble-factory/"')
    || !home.includes('href="/observatory/"')
    || !homeCard
    || !homeCard.kept
    || !/Not a certified toy/.test(homeCard.text);
  if (bad) process.exitCode = 1;
} finally {
  chrome.kill('SIGKILL');
  server.kill('SIGKILL');
}
