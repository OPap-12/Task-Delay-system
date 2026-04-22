// api.js — Centralized Fetch with JWT refresh, 401 handling, idempotency key stability
const BASE = '/api/v1';

// Central event bus
export const bus = {
  emit: (name, detail) => document.dispatchEvent(new CustomEvent(name, { detail })),
  on:   (name, fn)     => document.addEventListener(name, e => fn(e.detail)),
};

// Stable idempotency keys: same (taskId+action) always returns same key within session
const _idemKeys = new Map();
function getIdemKey(taskId, action) {
  const k = `${taskId}:${action}`;
  if (!_idemKeys.has(k)) _idemKeys.set(k, `${k}-${Date.now()}`);
  return _idemKeys.get(k);
}
export function resetIdemKey(taskId, action) {
  _idemKeys.delete(`${taskId}:${action}`);
}

function getToken()     { return localStorage.getItem('access_token'); }
function getRefresh()   { return localStorage.getItem('refresh_token'); }
function setTokens(a,r) { localStorage.setItem('access_token', a); if (r) localStorage.setItem('refresh_token', r); }

async function refreshToken() {
  const r = await fetch(`${BASE}/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: getRefresh() }),
  });
  if (r.ok) { const d = await r.json(); setTokens(d.access, null); return true; }
  return false;
}

async function request(method, path, body = null, idemKey = null, retry = true) {
  const headers = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` };
  if (idemKey) headers['Idempotency-Key'] = idemKey;
  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${BASE}${path}`, opts);

  // Auto-refresh on 401, retry once
  if (res.status === 401 && retry) {
    const ok = await refreshToken();
    if (ok) return request(method, path, body, idemKey, false);
    bus.emit('auth_expired', {});
    window.location.href = '/login/';
    return { status: 401, data: {} };
  }

  const data = await res.json().catch(() => ({}));
  return { status: res.status, data };
}

export const api = {
  getTasks:    (updatedAfter = null) => {
    const qs = updatedAfter ? `?updated_after=${encodeURIComponent(updatedAfter)}` : '';
    return request('GET', `/tasks/${qs}`);
  },
  getDashboard: () => request('GET', '/dashboard/metrics/'),
  getProfile:   () => request('GET', '/profile/'),
  patchStatus:  (taskId, action, reason = '') =>
    request('PATCH', `/tasks/${taskId}/status/`, { action, reason }, getIdemKey(taskId, action)),
};
