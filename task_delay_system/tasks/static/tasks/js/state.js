// state.js — In-memory task state store, guards stale overwrites
const _store = new Map(); // taskId → { status, updated_at }

export const state = {
  update(taskId, status, updatedAt) {
    const existing = _store.get(taskId);
    // Reject stale updates via updated_at comparison
    if (existing && updatedAt && existing.updated_at >= updatedAt) return false;
    _store.set(taskId, { status, updated_at: updatedAt || new Date().toISOString() });
    return true;
  },
  get(taskId) { return _store.get(taskId); },
  init(tasks) { tasks.forEach(t => _store.set(t.id, { status: t.status, updated_at: t.updated_at })); },
};
