// ws.js — WebSocket with backoff, heartbeat, updated_at-guarded delta resync
import { api } from './api.js';
import { state } from './state.js';
import { bus } from './api.js';

let socket = null;
let retries = 0;
let lastSeen = new Date().toISOString();
const MAX_RETRIES = 8;

function applyDelta(tasks) {
  tasks.forEach(t => {
    const changed = state.update(t.id, t.status, t.updated_at);
    if (changed) {
      const badge = document.querySelector(`[data-status-badge="${t.id}"]`);
      if (badge) badge.textContent = t.status;
    }
  });
}

export function connectWebSocket(userId, onMessage) {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  socket = new WebSocket(`${proto}://${location.host}/ws/notifications/`);

  window.addEventListener('beforeunload', () => {
    if (socket?.readyState === WebSocket.OPEN) socket.close();
  });

  socket.onopen = () => {
    retries = 0;
    // Delta resync: only fetch tasks updated since last seen — guarded by state store
    api.getTasks(lastSeen).then(({ data }) => {
      const tasks = data.results || data;
      if (Array.isArray(tasks) && tasks.length) {
        applyDelta(tasks);
        bus.emit('ws_resync', { count: tasks.length });
      }
    });
  };

  socket.onmessage = (e) => {
    lastSeen = new Date().toISOString();
    try {
      const msg = JSON.parse(e.data);
      if (msg.type === 'task_update' && msg.task_id) {
        // Inline WS push: guard with updated_at before touching DOM
        const changed = state.update(msg.task_id, msg.status, msg.updated_at);
        if (changed) {
          const badge = document.querySelector(`[data-status-badge="${msg.task_id}"]`);
          if (badge) badge.textContent = msg.status;
        }
      }
      onMessage(msg);
    } catch (_) {}
  };

  socket.onclose = () => {
    if (retries < MAX_RETRIES) {
      const delay = Math.min(1000 * Math.pow(2, retries), 30000);
      retries++;
      setTimeout(() => connectWebSocket(userId, onMessage), delay);
    } else {
      // Degrade gracefully: poll every 15s
      setInterval(() => {
        api.getTasks(lastSeen).then(({ data }) => {
          lastSeen = new Date().toISOString();
          applyDelta(data.results || data || []);
        });
      }, 15000);
    }
  };

  // Heartbeat to prevent proxy idle-timeout disconnects
  setInterval(() => {
    if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: 'ping' }));
  }, 30000);
}
