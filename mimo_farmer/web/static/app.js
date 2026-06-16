const app = document.querySelector('#app');
const wsStatus = document.querySelector('#ws-status');
const toastEl = document.querySelector('#toast');

const state = {
  route: '/',
  accountsPage: 1,
  lastProgress: 0,
  settings: null,
  logs: [],
  job: null,
};

const steps = [
  'Signup', 'Form', 'CAPTCHA', 'OTP Page', 'OTP Fetch', 'OTP Entry', 'Terms',
  'Balance', 'Referral', 'Risk Control', 'Balance', 'API Key', 'Save', 'Logout'
];

window.addEventListener('hashchange', route);
document.addEventListener('click', onGlobalClick);
route();
connectWs();

function route() {
  state.route = location.hash.replace(/^#/, '') || '/';
  document.querySelectorAll('.nav a').forEach(a => a.classList.toggle('active', a.dataset.route === state.route));
  if (state.route === '/') return renderDashboard();
  if (state.route === '/create') return renderCreate();
  if (state.route === '/accounts') return renderAccounts();
  if (state.route === '/batches') return renderBatches();
  if (state.route === '/settings') return renderSettings();
  renderDashboard();
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`;
    try { message = (await res.json()).detail || message; } catch (_) {}
    throw new Error(message);
  }
  return res.json();
}

function cloneTemplate(id) {
  app.replaceChildren(document.querySelector(`#${id}`).content.cloneNode(true));
}

async function renderDashboard() {
  cloneTemplate('dashboard-page');
  document.querySelector('[data-export="json"]').addEventListener('click', () => exportAccounts('json'));
  try {
    const data = await api('/api/stats');
    state.job = data.job;
    document.querySelector('#stats-grid').innerHTML = [
      statCard('Total Accounts', data.total_accounts),
      statCard('Today', data.accounts_today),
      statCard('Total Balance', money(data.total_balance)),
      statCard('Success Rate', `${data.success_rate}%`),
    ].join('');
    document.querySelector('#recent-list').innerHTML = data.recent_activity.length
      ? data.recent_activity.map(activityItem).join('')
      : '<p class="hint">No accounts yet.</p>';
    document.querySelector('#job-summary').innerHTML = jobSummary(data.job);
  } catch (err) {
    toast(err.message, true);
  }
}

function statCard(label, value) {
  return `<div class="stat-card"><div class="stat-label">${escapeHtml(label)}</div><div class="stat-value">${escapeHtml(String(value))}</div></div>`;
}

function activityItem(account) {
  return `<div class="activity-item"><div><strong>${escapeHtml(account.email)}</strong><br><span class="hint">${escapeHtml(account.created_at)}</span></div><div><span class="badge ${account.risk_control ? 'badge-error' : 'badge-success'}">${escapeHtml(account.status)}</span><br><strong>${escapeHtml(account.balance)}</strong></div></div>`;
}

function jobSummary(job) {
  if (!job) return '<p>No job yet.</p>';
  return `
    <div>Status: <span class="badge ${badgeClass(job.status)}">${escapeHtml(job.status)}</span></div>
    <div>Mode: ${escapeHtml(job.mode)}</div>
    <div>Created: ${job.total_created}</div>
    <div>Failed: ${job.total_failed}</div>
    <div>Started: ${escapeHtml(job.started_at || '-')}</div>
  `;
}

function renderCreate() {
  cloneTemplate('create-page');
  renderSteps();
  restoreLiveState();
  document.querySelector('#create-form').addEventListener('submit', startJob);
  document.querySelector('#cancel-job').addEventListener('click', cancelJob);
}

function renderSteps(current = 0) {
  const list = document.querySelector('#step-list');
  if (!list) return;
  list.innerHTML = steps.map((name, idx) => {
    const n = idx + 1;
    const cls = n < current ? 'done' : n === current ? 'running' : '';
    return `<div class="step ${cls}">${n}. ${escapeHtml(name)}</div>`;
  }).join('');
}

function restoreLiveState() {
  const log = document.querySelector('#live-log');
  if (log) log.textContent = state.logs.join('\n');
  updateProgress(state.lastProgress || 0);
  const status = document.querySelector('#job-status');
  if (status && state.job) {
    status.textContent = state.job.status;
    status.className = `badge ${badgeClass(state.job.status)}`;
  }
}

async function startJob(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = {
    mode: form.get('mode'),
    referral: form.get('referral'),
    count: Number(form.get('count') || 1),
    parallel: Number(form.get('parallel') || 1),
    password: form.get('password'),
    fast: form.get('fast') === 'on',
  };
  try {
    const data = await api('/api/create', { method: 'POST', body: JSON.stringify(payload) });
    state.job = data.job;
    state.logs = [];
    state.lastProgress = 0;
    restoreLiveState();
    toast('Job started');
  } catch (err) {
    toast(err.message, true);
  }
}

async function cancelJob() {
  try {
    const data = await api('/api/create/cancel', { method: 'POST', body: '{}' });
    state.job = data.job;
    toast('Cancel requested. Current browser step may finish first.');
  } catch (err) {
    toast(err.message, true);
  }
}

async function renderAccounts() {
  cloneTemplate('accounts-page');
  document.querySelector('#apply-filters').addEventListener('click', () => { state.accountsPage = 1; loadAccounts(); });
  document.querySelectorAll('[data-export]').forEach(btn => btn.addEventListener('click', () => exportAccounts(btn.dataset.export)));
  await loadAccounts();
}

async function loadAccounts() {
  const params = new URLSearchParams({ page: state.accountsPage, page_size: 50 });
  const search = document.querySelector('#search')?.value || '';
  const status = document.querySelector('#status-filter')?.value || '';
  const min = document.querySelector('#min-balance')?.value || '';
  const from = document.querySelector('#date-from')?.value || '';
  if (search) params.set('search', search);
  if (status) params.set('status', status);
  if (min) params.set('min_balance', min);
  if (from) params.set('date_from', from);
  try {
    const data = await api(`/api/accounts?${params}`);
    document.querySelector('#accounts-body').innerHTML = data.items.length ? data.items.map(accountRow).join('') : '<tr><td colspan="8">No accounts found.</td></tr>';
    renderPagination(data);
  } catch (err) {
    toast(err.message, true);
  }
}

function accountRow(account) {
  const credential = `${account.email}\n${account.password}\n${account.api_key}`;
  return `<tr>
    <td class="code">${escapeHtml(account.email)}</td>
    <td class="code">${escapeHtml(account.password)}</td>
    <td class="code">${escapeHtml(maskKey(account.api_key))}</td>
    <td class="code">${escapeHtml(account.referral || account.own_referral || '-')}</td>
    <td><strong>${escapeHtml(account.balance)}</strong></td>
    <td><span class="badge ${account.risk_control ? 'badge-error' : 'badge-success'}">${escapeHtml(account.status)}</span></td>
    <td>${escapeHtml(account.created_at)}</td>
    <td><button class="btn btn-secondary" data-copy="${escapeAttr(credential)}">Copy</button></td>
  </tr>`;
}

function renderPagination(data) {
  const el = document.querySelector('#pagination');
  el.innerHTML = `
    <button class="btn btn-secondary" id="prev-page" ${data.page <= 1 ? 'disabled' : ''}>Prev</button>
    <strong>Page ${data.page} / ${Math.max(1, data.pages)} (${data.total})</strong>
    <button class="btn btn-secondary" id="next-page" ${data.page >= data.pages ? 'disabled' : ''}>Next</button>
  `;
  document.querySelector('#prev-page').addEventListener('click', () => { state.accountsPage--; loadAccounts(); });
  document.querySelector('#next-page').addEventListener('click', () => { state.accountsPage++; loadAccounts(); });
}

async function renderBatches() {
  cloneTemplate('batches-page');
  try {
    const data = await api('/api/batches');
    document.querySelector('#batches-body').innerHTML = data.items.length ? data.items.map(batchRow).join('') : '<tr><td colspan="7">No batches found.</td></tr>';
  } catch (err) {
    toast(err.message, true);
  }
}

function batchRow(batch) {
  return `<tr>
    <td class="code">${escapeHtml(batch.filename)}</td>
    <td><span class="badge badge-info">${escapeHtml(batch.mode)}</span></td>
    <td>${batch.total_accounts}</td>
    <td>${batch.success_count}</td>
    <td>${batch.fail_count}</td>
    <td>${money(batch.total_balance)}</td>
    <td>${escapeHtml(batch.created_at)}</td>
  </tr>`;
}

async function renderSettings() {
  cloneTemplate('settings-page');
  const form = document.querySelector('#settings-form');
  try {
    const data = await api('/api/settings');
    state.settings = data.settings;
    form.default_referral.value = data.settings.default_referral || '';
    form.default_password.value = data.settings.default_password || '';
    form.ip_rotation_interval.value = data.settings.ip_rotation_interval || 5;
    form.email_domains.value = (data.settings.email_domains || []).join(', ');
    form.fast_default.checked = Boolean(data.settings.fast_default);
    form.headless.checked = Boolean(data.settings.headless);
    document.querySelector('#settings-note').textContent = `Accounts directory: ${data.accounts_dir}`;
  } catch (err) {
    toast(err.message, true);
  }
  form.addEventListener('submit', saveSettings);
}

async function saveSettings(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = {
    default_referral: form.default_referral.value,
    default_password: form.default_password.value,
    ip_rotation_interval: Number(form.ip_rotation_interval.value || 5),
    email_domains: form.email_domains.value.split(',').map(s => s.trim()).filter(Boolean),
    fast_default: form.fast_default.checked,
    headless: form.headless.checked,
  };
  try {
    await api('/api/settings', { method: 'PUT', body: JSON.stringify(payload) });
    toast('Settings saved for this server session');
  } catch (err) {
    toast(err.message, true);
  }
}

function connectWs() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${proto}://${location.host}/ws/progress`);
  ws.addEventListener('open', () => {
    wsStatus.textContent = 'WS live';
    wsStatus.className = 'badge badge-success';
  });
  ws.addEventListener('close', () => {
    wsStatus.textContent = 'WS reconnecting';
    wsStatus.className = 'badge badge-warning';
    setTimeout(connectWs, 1500);
  });
  ws.addEventListener('message', event => {
    try { handleWs(JSON.parse(event.data)); } catch (_) {}
  });
}

function handleWs(message) {
  if (message.type === 'progress') {
    const data = message.data;
    state.lastProgress = data.progress_pct;
    state.logs.push(data.log || data.message);
    state.logs = state.logs.slice(-500);
    if (state.route === '/create') {
      updateProgress(data.progress_pct);
      renderSteps(data.step);
      const log = document.querySelector('#live-log');
      if (log) {
        log.textContent = state.logs.join('\n');
        log.scrollTop = log.scrollHeight;
      }
      const status = document.querySelector('#job-status');
      if (status) {
        status.textContent = data.status;
        status.className = `badge ${badgeClass(data.status)}`;
      }
    }
  }
  if (message.type === 'account_created') toast(`Created ${message.data.email}`);
  if (message.type === 'job_started' || message.type === 'job_cancel_requested') state.job = message.data;
  if (message.type === 'job_complete') {
    state.job = { ...(state.job || {}), ...message.data };
    updateProgress(100);
    toast(`Job ${message.data.status}: ${message.data.total_created} created, ${message.data.total_failed} failed`);
  }
  if (message.type === 'job_error') toast(message.data.message, true);
}

function updateProgress(value) {
  const bar = document.querySelector('#progress-bar');
  if (!bar) return;
  bar.style.width = `${value}%`;
  bar.textContent = `${value}%`;
}

function onGlobalClick(event) {
  const copy = event.target.closest('[data-copy]');
  if (copy) {
    navigator.clipboard.writeText(copy.dataset.copy).then(() => toast('Copied'));
  }
}

function exportAccounts(format) {
  const params = new URLSearchParams({ format });
  const search = document.querySelector('#search')?.value || '';
  const status = document.querySelector('#status-filter')?.value || '';
  const min = document.querySelector('#min-balance')?.value || '';
  const from = document.querySelector('#date-from')?.value || '';
  if (search) params.set('search', search);
  if (status) params.set('status', status);
  if (min) params.set('min_balance', min);
  if (from) params.set('date_from', from);
  window.location.href = `/api/export?${params}`;
}

function badgeClass(status) {
  if (status === 'completed' || status === 'active' || status === 'running') return 'badge-success';
  if (status === 'failed' || status === 'risk_controlled') return 'badge-error';
  if (status === 'cancelled') return 'badge-warning';
  return 'badge-info';
}

function maskKey(key) {
  if (!key) return '';
  return key.length > 22 ? `${key.slice(0, 12)}...${key.slice(-6)}` : key;
}

function money(value) {
  const number = Number(value || 0);
  return `$${number.toFixed(2)}`;
}

function toast(message, error = false) {
  toastEl.textContent = message;
  toastEl.hidden = false;
  toastEl.style.background = error ? 'var(--destructive)' : 'var(--secondary)';
  toastEl.style.color = error ? '#fff' : 'var(--text)';
  clearTimeout(toastEl._timer);
  toastEl._timer = setTimeout(() => { toastEl.hidden = true; }, 3500);
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/`/g, '&#96;');
}
