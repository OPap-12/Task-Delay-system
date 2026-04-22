// actions.js — FSM dispatcher with loading states, double-click guard, meaningful errors
import { api, bus, resetIdemKey } from './api.js';
import { state } from './state.js';

const FSM_ERRORS = {
  'Cannot submit': 'Task is not in a submittable state.',
  'Cannot approve': 'Task must be in review before approving.',
  'Cannot reject': 'Task must be in review before rejecting.',
  'Only the assigned': 'Only the assigned employee can perform this action.',
  'Only active Admins': 'Only managers can reassign tasks.',
  'default': 'This action is not allowed in the current task state.',
};

function humanizeError(raw = '') {
  for (const [key, msg] of Object.entries(FSM_ERRORS)) {
    if (raw.includes(key)) return msg;
  }
  return FSM_ERRORS.default;
}

export function showToast(msg, type = 'success') {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.className = `toast toast--${type} toast--visible`;
  setTimeout(() => el.classList.remove('toast--visible'), 4500);
}

function setLoading(btn, loading) {
  if (!btn) return;
  btn.disabled = loading;
  btn.dataset.originalText = btn.dataset.originalText || btn.textContent;
  btn.textContent = loading ? 'Processing…' : btn.dataset.originalText;
}

async function dispatchAction(taskId, action, reason = '') {
  const btn = document.querySelector(`[data-task-id="${taskId}"][data-action="${action}"]`);
  setLoading(btn, true);

  const { status, data } = await api.patchStatus(taskId, action, reason);

  if (status === 200) {
    if (data.note === 'idempotent_hit') {
      showToast('Already processed — no duplicate action taken.', 'info');
    } else {
      // New successful transition — reset key so next genuine retry gets a fresh key
      resetIdemKey(taskId, action);
      const changed = state.update(taskId, data.task_status, data.updated_at);
      if (changed) {
        const badge = document.querySelector(`[data-status-badge="${taskId}"]`);
        if (badge) badge.textContent = data.task_status;
      }
      showToast(`Task ${action}d successfully.`, 'success');
      bus.emit('task_updated', { taskId, status: data.task_status });
    }
  } else if (status >= 400 && status < 500) {
    showToast(humanizeError(data.error || data.detail || ''), 'error');
  } else {
    showToast('Server error. Please try again.', 'error');
  }

  setLoading(btn, false);
}

export function initActions() {
  document.querySelectorAll('[data-task-id][data-action]').forEach(btn => {
    btn.addEventListener('click', () => {
      const { taskId, action } = btn.dataset;
      const reason = action === 'reject' ? (prompt('Rejection reason:') || '') : '';
      dispatchAction(taskId, action, reason);
    });
  });
}
