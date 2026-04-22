// main.js — Entry point, wires all modules via event bus
import { api, bus } from './api.js';
import { state } from './state.js';
import { connectWebSocket } from './ws.js';
import { initActions, showToast } from './actions.js';

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Hydrate in-memory state from server-rendered task data
  const initialTasks = window.__TASK_STATE__ || [];
  state.init(initialTasks);

  // 2. Attach FSM action buttons
  initActions();

  // 3. Connect WebSocket with full delta-resync + backoff
  const userId = document.body.dataset.userId;
  if (userId) {
    connectWebSocket(userId, (msg) => {
      if (msg.title) showToast(`${msg.title}: ${msg.message || ''}`, 'info');
    });
  }

  // 4. Live dashboard metrics (only on dashboard page)
  const metricsEl = document.getElementById('dashboard-metrics');
  if (metricsEl) {
    const { status, data } = await api.getDashboard();
    if (status === 200) {
      document.getElementById('metric-total')?.setAttribute('data-value', data.total ?? 0);
      document.getElementById('metric-pending')?.setAttribute('data-value', data.pending ?? 0);
      document.getElementById('metric-progress')?.setAttribute('data-value', data.in_progress ?? 0);
      document.getElementById('metric-done')?.setAttribute('data-value', data.completed ?? 0);
    }
  }

  // 5. Listen to cross-module events
  bus.on('task_updated', ({ taskId, status }) => {
    console.log(`[State] Task ${taskId} → ${status}`);
  });
  bus.on('ws_resync', ({ count }) => {
    showToast(`Synced ${count} update(s) on reconnect.`, 'info');
  });
});
