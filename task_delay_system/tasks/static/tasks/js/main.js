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
      if (msg.title) addDropdownAlert(msg.title, msg.message || '', 'info');
      updateBell();
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


// --- UI Logic Migrated from base.html ---

// Bell State
let notifCount = 0;
function updateBell() {
    const badge = document.getElementById('notif-badge');
    const bell = document.getElementById('bell-container');
    if (!badge || !bell) return;
    notifCount++;
    badge.innerText = notifCount > 9 ? '9+' : notifCount;
    badge.style.display = 'flex';
    badge.classList.add('pulse');
    setTimeout(() => badge.classList.remove('pulse'), 1200);
    bell.classList.remove('empty');
    bell.classList.add('has-notifs', 'ringing');
    setTimeout(() => bell.classList.remove('ringing'), 500);
}

function addDropdownAlert(title, message, type) {
    const list = document.getElementById('notif-list');
    if (!list) return;
    if (notifCount === 0) list.innerHTML = '';
    const item = document.createElement('li');
    item.className = 'notif-item ' + (type || '');
    const titleEl = document.createElement('strong');
    titleEl.textContent = title;
    item.appendChild(titleEl);
    item.appendChild(document.createTextNode(' ' + message));
    list.prepend(item);
}

document.addEventListener('DOMContentLoaded', () => {
    // Notifications toggle
    const bell = document.getElementById('bell-container');
    if (bell) {
        bell.addEventListener('click', (e) => {
            e.stopPropagation();
            const dropdown = document.getElementById('notif-dropdown');
            if (dropdown) {
                dropdown.classList.toggle('active');
                if (dropdown.classList.contains('active')) {
                    notifCount = 0;
                    const badge = document.getElementById('notif-badge');
                    if (badge) badge.style.display = 'none';
                    bell.classList.remove('has-notifs');
                    bell.classList.add('empty');
                }
            }
        });
    }

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        if (bell && !bell.contains(e.target)) {
            const dropdown = document.getElementById('notif-dropdown');
            if (dropdown) dropdown.classList.remove('active');
        }
    });

    // Auto-dismiss initial toasts
    document.querySelectorAll('.toast.show').forEach((t) => {
        setTimeout(() => {
            t.classList.remove('show');
            t.classList.add('hide');
            setTimeout(() => t.remove(), 300);
        }, 4000);
    });

    // Close sidebar on mobile when clicking main area
    const mainArea = document.querySelector('.main-area');
    if (mainArea) {
        mainArea.addEventListener('click', () => {
            const sidebar = document.getElementById('sidebar');
            if (sidebar) sidebar.classList.remove('open');
        });
    }
});

// Phase 1: Global Form Guards & Recovery
document.addEventListener('submit', (e) => {
    const form = e.target;
    if (form.dataset.submitted === 'true') {
        e.preventDefault();
        return;
    }
    if (e.defaultPrevented) return;

    const btn = form.querySelector('button[type="submit"]');
    if (btn) {
        setTimeout(() => {
            if (e.defaultPrevented) return;
            form.dataset.submitted = 'true';
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-small"></span> Processing...';
            const row = form.closest('tr');
            if (row) row.classList.add('submitting-row');
        }, 10);
    }
});

// Clear submission guard on browser invalid form
document.addEventListener('invalid', (e) => {
    const form = e.target.form;
    if (form) {
        form.removeAttribute('data-submitted');
        const btn = form.querySelector('button[type="submit"]');
        if (btn) {
            btn.disabled = false;
            if (btn.dataset.originalText) {
                btn.innerHTML = btn.dataset.originalText;
            } else {
                btn.innerHTML = btn.textContent.replace(' Processing...', '');
            }
        }
        const row = form.closest('tr');
        if (row) row.classList.remove('submitting-row');
    }
}, true);

window.addEventListener('pageshow', () => {
    document.querySelectorAll('button[disabled]').forEach(btn => btn.disabled = false);
    document.querySelectorAll('form[data-submitted]').forEach(form => delete form.dataset.submitted);
    document.querySelectorAll('.submitting-row').forEach(row => row.classList.remove('submitting-row'));
});

// Phase 2: Top Progress Bar Trigger
document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href]');
    if (link && link.target !== '_blank' && !link.getAttribute('href').startsWith('#')) {
        document.body.classList.add('loading');
    }
});

// Modals & Focus Traps
function setupFocusTrap(modal) {
    const focusable = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    
    modal.onkeydown = function(e) {
        if (e.key === 'Tab') {
            if (e.shiftKey) {
                if (document.activeElement === first) { e.preventDefault(); last.focus(); }
            } else {
                if (document.activeElement === last) { e.preventDefault(); first.focus(); }
            }
        }
        if (e.key === 'Escape') { modal.style.display = 'none'; }
    };
    // small delay to let display:flex render
    setTimeout(() => {
        const input = modal.querySelector('textarea, input');
        if (input) input.focus();
        else first.focus();
    }, 50);
}

window.openRejectModal = function(url) {
    const modal = document.getElementById('reject-modal');
    const form = document.getElementById('reject-form');
    if (!modal || !form) return;
    form.action = url;
    form.querySelector('textarea').value = '';
    modal.style.display = 'flex';
    setupFocusTrap(modal);
};

window.openLogoutModal = function() {
    const modal = document.getElementById('logout-modal');
    if (!modal) return;
    modal.style.display = 'flex';
    setupFocusTrap(modal);
};

// Close modals on backdrop click or escape
document.addEventListener('click', (e) => {
    if (e.target.id === 'reject-modal' || e.target.id === 'logout-modal') {
        e.target.style.display = 'none';
    }
});
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const rm = document.getElementById('reject-modal');
        const lm = document.getElementById('logout-modal');
        if (rm && rm.style.display === 'flex') rm.style.display = 'none';
        if (lm && lm.style.display === 'flex') lm.style.display = 'none';
    }
});
