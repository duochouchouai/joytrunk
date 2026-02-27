<template>
  <div class="page">
    <div class="page-header">
      <router-link to="/app/employees" class="back-link">{{ t('logs.backToEmployees') }}</router-link>
      <h1 class="page-title">{{ t('logs.title') }} · {{ employeeName || employeeId }}</h1>
      <button type="button" class="btn secondary" :disabled="loading" @click="loadLogs">
        {{ loading ? t('common.loading') : t('common.refresh') }}
      </button>
    </div>
    <div class="card">
      <p v-if="loadError" class="error">{{ loadError }}</p>
      <p v-else-if="!loading && rawEntries.length === 0" class="muted">{{ t('logs.empty') }}</p>
      <template v-else>
        <div class="log-toolbar">
          <div class="toolbar-row">
            <label class="toolbar-label">{{ t('logs.sortOrder') }}</label>
            <select v-model="sortOrder" class="toolbar-select">
              <option value="desc">{{ t('logs.sortNewestFirst') }}</option>
              <option value="asc">{{ t('logs.sortOldestFirst') }}</option>
            </select>
          </div>
          <div class="toolbar-row">
            <label class="toolbar-label">{{ t('logs.filterByEvent') }}</label>
            <div class="event-filters">
              <label v-for="ev in eventTypeOptions" :key="ev.value" class="event-check">
                <input type="checkbox" :value="ev.value" v-model="filterEventTypes" />
                <span>{{ eventLabel(ev.value) }}</span>
              </label>
            </div>
          </div>
          <div class="toolbar-row">
            <label class="toolbar-label">{{ t('logs.filterByRunId') }}</label>
            <input
              v-model.trim="filterRunId"
              type="text"
              class="toolbar-input"
              :placeholder="t('logs.filterPlaceholderRunId')"
            />
          </div>
          <div class="toolbar-row">
            <label class="toolbar-label">{{ t('logs.filterByKeyword') }}</label>
            <input
              v-model.trim="filterKeyword"
              type="text"
              class="toolbar-input"
              :placeholder="t('logs.filterPlaceholderKeyword')"
            />
          </div>
          <p class="result-count">{{ t('logs.resultCount', { n: filteredAndSortedEntries.length }) }}</p>
        </div>
        <div class="log-list">
          <div
            v-for="(entry, index) in filteredAndSortedEntries"
            :key="index"
            class="log-entry"
            :data-event="entry.event"
          >
            <div class="log-meta">
              <span class="log-ts" :title="entry.ts">{{ formatTs(entry.ts) }}</span>
              <span class="log-event" :class="eventClass(entry.event)">{{ eventLabel(entry.event) }}</span>
              <span v-if="entry.run_id" class="log-run-id" :title="entry.run_id">{{ entry.run_id.slice(0, 8) }}</span>
            </div>
            <div v-if="Object.keys(entry.payload || {}).length" class="log-payload">
              <pre>{{ formatPayload(entry.payload) }}</pre>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from '../api'

const { t } = useI18n()
const route = useRoute()
const employeeId = computed(() => route.params.id)
const rawEntries = ref([])
const loading = ref(false)
const loadError = ref('')
const employeeName = ref('')
const sortOrder = ref('desc')
const filterEventTypes = ref([])
const filterRunId = ref('')
const filterKeyword = ref('')

const EVENT_TYPES = [
  'loop_start', 'iteration', 'llm_request', 'llm_response',
  'tool_calls', 'tool_result', 'final_reply', 'max_iterations',
  'loop_done', 'append_turn_done',
]
const eventTypeOptions = EVENT_TYPES.map((value) => ({ value }))

const filteredAndSortedEntries = computed(() => {
  let list = rawEntries.value
  if (filterEventTypes.value.length > 0) {
    const set = new Set(filterEventTypes.value)
    list = list.filter((e) => set.has(e.event))
  }
  if (filterRunId.value) {
    const q = filterRunId.value.toLowerCase()
    list = list.filter((e) => e.run_id && e.run_id.toLowerCase().includes(q))
  }
  if (filterKeyword.value) {
    const q = filterKeyword.value.toLowerCase()
    list = list.filter((e) => {
      const str = [
        e.ts,
        e.event,
        e.run_id,
        typeof e.payload === 'object' ? JSON.stringify(e.payload) : String(e.payload),
      ].filter(Boolean).join(' ')
      return str.toLowerCase().includes(q)
    })
  }
  const sorted = [...list].sort((a, b) => {
    const tA = a.ts || ''
    const tB = b.ts || ''
    return sortOrder.value === 'asc' ? (tA < tB ? -1 : tA > tB ? 1 : 0) : (tB < tA ? -1 : tB > tA ? 1 : 0)
  })
  return sorted
})

const eventLabels = {
  loop_start: 'logs.eventLoopStart',
  iteration: 'logs.eventIteration',
  llm_request: 'logs.eventLlmRequest',
  llm_response: 'logs.eventLlmResponse',
  tool_calls: 'logs.eventToolCalls',
  tool_result: 'logs.eventToolResult',
  final_reply: 'logs.eventFinalReply',
  max_iterations: 'logs.eventMaxIterations',
  loop_done: 'logs.eventLoopDone',
  append_turn_done: 'logs.eventAppendTurnDone',
}

function eventLabel(event) {
  return t(eventLabels[event] || event)
}

function eventClass(event) {
  return `event-${(event || '').replace(/_/g, '-')}`
}

function formatTs(ts) {
  if (!ts) return ''
  try {
    const d = new Date(ts)
    return d.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'medium' })
  } catch {
    return ts
  }
}

function formatPayload(payload) {
  if (!payload || typeof payload !== 'object') return ''
  return JSON.stringify(payload, null, 2)
}

async function loadLogs() {
  if (!employeeId.value) return
  loading.value = true
  loadError.value = ''
  try {
    const data = await api.employees.logs(employeeId.value)
    rawEntries.value = Array.isArray(data.entries) ? data.entries : []
  } catch (e) {
    loadError.value = e.message || t('logs.loadFailed')
    rawEntries.value = []
  } finally {
    loading.value = false
  }
}

async function loadEmployeeName() {
  if (!employeeId.value) return
  try {
    const team = await api.teams.current()
    const emp = (team.employees || []).find((e) => e.id === employeeId.value)
    employeeName.value = emp ? emp.name : ''
  } catch {
    employeeName.value = ''
  }
}

onMounted(() => {
  loadEmployeeName()
  loadLogs()
})
watch(employeeId, () => {
  loadEmployeeName()
  loadLogs()
})
</script>

<style scoped>
.page { max-width: 900px; }
.page-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1.25rem;
}
.back-link {
  color: var(--jt-primary);
  text-decoration: none;
  font-size: 0.9375rem;
}
.back-link:hover { text-decoration: underline; }
.page-title { margin: 0; font-size: 1.25rem; font-weight: 600; flex: 1; }
.btn { padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.9375rem; cursor: pointer; border: 1px solid var(--jt-border); background: var(--jt-card-bg); }
.btn.secondary:hover:not(:disabled) { background: var(--jt-border); }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.card {
  background: var(--jt-card-bg);
  border-radius: var(--jt-radius);
  box-shadow: var(--jt-card-shadow);
  padding: 1.25rem 1.5rem;
}
.error { color: #b91c1c; font-size: 0.875rem; margin: 0; }
.muted { font-size: 0.9375rem; color: var(--jt-text-muted); margin: 0; }
.log-toolbar {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--jt-border);
}
.toolbar-row { margin-bottom: 0.75rem; }
.toolbar-row:last-of-type { margin-bottom: 0.5rem; }
.toolbar-label { display: inline-block; font-size: 0.8125rem; font-weight: 500; color: var(--jt-text-muted); margin-right: 0.5rem; min-width: 5rem; }
.toolbar-select, .toolbar-input {
  padding: 0.35rem 0.5rem;
  border: 1px solid var(--jt-border);
  border-radius: 6px;
  font-size: 0.875rem;
  background: var(--jt-card-bg);
}
.toolbar-select { min-width: 10rem; }
.toolbar-input { min-width: 12rem; }
.event-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
}
.event-check {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8125rem;
  cursor: pointer;
}
.event-check input { cursor: pointer; }
.result-count { font-size: 0.8125rem; color: var(--jt-text-muted); margin: 0; }
.log-list { display: flex; flex-direction: column; gap: 0.75rem; }
.log-entry {
  border: 1px solid var(--jt-border);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
}
.log-meta { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.35rem; }
.log-ts { color: var(--jt-text-muted); font-family: ui-monospace, monospace; }
.log-event {
  font-weight: 500;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8125rem;
}
.log-event.event-loop-start { background: rgba(15, 118, 110, 0.15); color: var(--jt-primary); }
.log-event.event-iteration { background: rgba(59, 130, 246, 0.15); color: #2563eb; }
.log-event.event-llm-request { background: rgba(14, 165, 233, 0.2); color: #0369a1; }
.log-event.event-llm-response { background: rgba(34, 197, 94, 0.15); color: #15803d; }
.log-event.event-tool-calls { background: rgba(168, 85, 247, 0.15); color: #7c3aed; }
.log-event.event-tool-result { background: rgba(34, 197, 94, 0.15); color: #16a34a; }
.log-event.event-final-reply { background: rgba(234, 179, 8, 0.15); color: #a16207; }
.log-event.event-loop-done { background: rgba(15, 118, 110, 0.2); color: var(--jt-primary); }
.log-event.event-append-turn-done { background: rgba(107, 114, 128, 0.15); color: #4b5563; }
.log-run-id { font-family: ui-monospace, monospace; color: var(--jt-text-muted); font-size: 0.75rem; }
.log-payload { margin-top: 0.5rem; }
.log-payload pre {
  margin: 0;
  padding: 0.5rem;
  background: var(--jt-bg);
  border-radius: 4px;
  overflow-x: auto;
  font-size: 0.8125rem;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
