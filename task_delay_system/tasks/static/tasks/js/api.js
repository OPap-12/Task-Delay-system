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

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function request(method, path, body = null, idemKey = null, retry = true) {
  const headers = { 'Content-Type': 'application/json' };
  
  if (idemKey) headers['Idempotency-Key'] = idemKey;
  
  // Add CSRF token for state-changing requests
  if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method.toUpperCase())) {
      headers['X-CSRFToken'] = getCookie('csrftoken');
  }

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${BASE}${path}`, opts);

  // If unauthorized via session cookie, redirect to login
  if ((res.status === 401 || res.status === 403) && retry) {
    bus.emit('auth_expired', {});
    window.location.href = '/login/';
    return { status: res.status, data: {} };
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
