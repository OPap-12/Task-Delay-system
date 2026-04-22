import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.BASE_URL || 'https://task-delay-system.onrender.com';
const TASK_ID = __ENV.TASK_ID || '1';
const AUTH = __ENV.AUTH;

export const options = {
  scenarios: {
    same_key_race: {
      executor: 'constant-vus',
      vus: 50,
      duration: '30s',
      exec: 'sameKeyRace',
    },
    different_keys_race: {
      executor: 'constant-vus',
      vus: 50,
      duration: '30s',
      startTime: '35s',
      exec: 'differentKeysRace',
    },
    list_delta: {
      executor: 'constant-vus',
      vus: 20,
      duration: '30s',
      startTime: '70s',
      exec: 'deltaFetch',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<800'],
    checks: ['rate>0.99'],          // >99% of checks must pass (covers 200+4xx)
  },
};

function patchStatus(idemKey) {
  const url = `${BASE}/api/v1/tasks/${TASK_ID}/status/`;
  const payload = JSON.stringify({ action: 'approve' });
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': AUTH,
      'Idempotency-Key': idemKey,
    },
    timeout: '30s',
  };
  return http.patch(url, payload, params);
}

export function sameKeyRace() {
  const key = 'fixed-key-123';
  const res = patchStatus(key);
  check(res, {
    '200 OK': (r) => r.status === 200,
    'idempotent or success': (r) => {
      try {
        const j = r.json();
        return j && (j.note === 'idempotent_hit' || j.status === 'success');
      } catch (_) { return true; }
    },
  });
  sleep(0.2);
}

export function differentKeysRace() {
  const key = Math.random().toString(36).slice(2);
  const res = patchStatus(key);
  check(res, {
    '200 or 4xx only': (r) => r.status === 200 || (r.status >= 400 && r.status < 500),
    'no 5xx': (r) => r.status < 500,
  });
  sleep(0.2);
}

export function deltaFetch() {
  const ts = new Date(Date.now() - 60 * 1000).toISOString();
  const url = `${BASE}/api/v1/tasks/?updated_after=${encodeURIComponent(ts)}`;
  const res = http.get(url, {
    headers: { 'Authorization': AUTH },
    timeout: '30s',
  });
  check(res, {
    '200 OK': (r) => r.status === 200,
    'valid JSON': (r) => { try { r.json(); return true; } catch (_) { return false; } },
  });
  sleep(0.5);
}
