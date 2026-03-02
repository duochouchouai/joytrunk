<template>
  <div class="page">
    <div class="page-header">
      <router-link to="/employees" class="back-link">{{ t('memory.backToEmployees') }}</router-link>
      <h1 class="page-title">{{ t('memory.title') }} · {{ employeeName || employeeId }}</h1>
      <button type="button" class="btn secondary" :disabled="loading" @click="loadMemory">
        {{ loading ? t('common.loading') : t('common.refresh') }}
      </button>
    </div>
    <div class="card">
      <p v-if="loadError" class="error">{{ loadError }}</p>
      <p v-else-if="!loading && !data" class="muted">{{ t('memory.empty') }}</p>
      <template v-else-if="data">
        <section class="memory-section">
          <div class="section-head">
            <h2 class="section-title">{{ t('memory.categories') }} ({{ (data.categories || []).length }})</h2>
            <button type="button" class="btn small" @click="openForm('category', 'add')">{{ t('memory.add') }}</button>
          </div>
          <div v-if="formMode && formMode.section === 'category'" class="form-card">
            <input v-model="formData.name" type="text" :placeholder="t('memory.name')" class="input" />
            <input v-model="formData.description" type="text" :placeholder="t('memory.description')" class="input" />
            <textarea v-model="formData.summary" :placeholder="t('memory.summary')" class="input" rows="2"></textarea>
            <div class="form-actions">
              <button type="button" class="btn primary" :disabled="mutateLoading" @click="submitCategoryForm">{{ t('memory.save') }}</button>
              <button type="button" class="btn secondary" @click="closeForm">{{ t('memory.cancel') }}</button>
            </div>
            <p v-if="mutateError" class="error small">{{ mutateError }}</p>
          </div>
          <div class="category-list">
            <div
              v-for="c in (data.categories || [])"
              :key="c.id"
              class="category-block"
            >
              <div class="memory-card card-with-actions category-header">
                <div class="meta-row"><span class="meta-id">{{ c.id }}</span><span class="meta-ts muted">{{ formatTs(c.created_at) }}</span></div>
                <div class="card-name">{{ c.name }}</div>
                <div v-if="c.description" class="card-desc muted">{{ c.description }}</div>
                <div v-if="c.summary" class="card-summary">{{ truncate(c.summary, 500) }}</div>
                <div class="card-actions">
                  <button type="button" class="btn-link" @click="openForm('category', 'edit', c)">{{ t('memory.edit') }}</button>
                  <button type="button" class="btn-link danger" @click="deleteCategory(c.id)">{{ t('memory.delete') }}</button>
                </div>
              </div>
              <div class="category-items-wrap">
                <p v-if="itemsInCategory(c.id).length === 0" class="muted category-empty">{{ t('memory.noItemsInCategory') }}</p>
                <ul v-else class="category-items-list">
                  <li v-for="i in itemsInCategory(c.id)" :key="i.id" class="category-item-row">
                    <span class="item-type-tag">{{ i.memory_type }}</span>
                    <span class="item-summary-text">{{ truncate(i.summary, 120) }}</span>
                    <span class="muted small">{{ formatTs(i.created_at) }}</span>
                    <button type="button" class="btn-link" @click="openForm('item', 'edit', i)">{{ t('memory.edit') }}</button>
                    <button type="button" class="btn-link danger" @click="deleteItem(i.id)">{{ t('memory.delete') }}</button>
                  </li>
                </ul>
                <button type="button" class="btn small add-item-btn" @click="openFormForItemInCategory(c.id)">{{ t('memory.addItemToCategory') }}</button>
              </div>
              <div v-if="formMode && formMode.section === 'item' && formMode.addToCategoryId === c.id" class="form-card category-inline-form">
                <input v-model="formData.memory_type" type="text" :placeholder="t('memory.memoryType')" class="input" />
                <textarea v-model="formData.summary" :placeholder="t('memory.summary')" class="input" rows="2"></textarea>
                <input v-model="formData.resource_id" type="text" :placeholder="'resource_id (可选)'" class="input" />
                <div class="form-actions">
                  <button type="button" class="btn primary" :disabled="mutateLoading" @click="submitItemForm">{{ t('memory.save') }}</button>
                  <button type="button" class="btn secondary" @click="closeForm">{{ t('memory.cancel') }}</button>
                </div>
                <p v-if="mutateError" class="error small">{{ mutateError }}</p>
              </div>
            </div>
          </div>
        </section>
        <section class="memory-section">
          <div class="section-head">
            <h2 class="section-title">{{ t('memory.items') }} ({{ (data.items || []).length }})</h2>
            <button type="button" class="btn small" @click="openForm('item', 'add')">{{ t('memory.add') }}</button>
          </div>
          <div v-if="formMode && formMode.section === 'item' && !formMode.addToCategoryId" class="form-card">
            <input v-model="formData.memory_type" type="text" :placeholder="t('memory.memoryType')" class="input" />
            <textarea v-model="formData.summary" :placeholder="t('memory.summary')" class="input" rows="2"></textarea>
            <input v-model="formData.resource_id" type="text" :placeholder="'resource_id (可选)'" class="input" />
            <div class="form-actions">
              <button type="button" class="btn primary" :disabled="mutateLoading" @click="submitItemForm">{{ t('memory.save') }}</button>
              <button type="button" class="btn secondary" @click="closeForm">{{ t('memory.cancel') }}</button>
            </div>
            <p v-if="mutateError" class="error small">{{ mutateError }}</p>
          </div>
          <div class="item-list">
            <div
              v-for="i in (data.items || [])"
              :key="i.id"
              class="memory-card item-card card-with-actions"
            >
              <div class="meta-row"><span class="item-type">{{ i.memory_type }}</span><span class="item-ts muted">{{ formatTs(i.created_at) }}</span></div>
              <div class="meta-id small">{{ i.id }}</div>
              <div class="item-summary">{{ i.summary }}</div>
              <div v-if="i.resource_id" class="muted small">resource_id: {{ i.resource_id }}</div>
              <div v-if="i.extra && Object.keys(i.extra).length" class="muted small pre">{{ JSON.stringify(i.extra) }}</div>
              <div class="card-actions">
                <button type="button" class="btn-link" @click="openForm('item', 'edit', i)">{{ t('memory.edit') }}</button>
                <button type="button" class="btn-link danger" @click="deleteItem(i.id)">{{ t('memory.delete') }}</button>
              </div>
            </div>
          </div>
        </section>
        <section class="memory-section">
          <div class="section-head">
            <h2 class="section-title">{{ t('memory.resources') }} ({{ (data.resources || []).length }})</h2>
            <button type="button" class="btn small" @click="openForm('resource', 'add')">{{ t('memory.add') }}</button>
          </div>
          <div v-if="formMode && formMode.section === 'resource'" class="form-card">
            <input v-model="formData.url" type="text" :placeholder="t('memory.url')" class="input" />
            <input v-model="formData.modality" type="text" :placeholder="t('memory.modality')" class="input" />
            <input v-model="formData.local_path" type="text" placeholder="local_path" class="input" />
            <input v-model="formData.caption" type="text" :placeholder="t('memory.caption')" class="input" />
            <div class="form-actions">
              <button type="button" class="btn primary" :disabled="mutateLoading" @click="submitResourceForm">{{ t('memory.save') }}</button>
              <button type="button" class="btn secondary" @click="closeForm">{{ t('memory.cancel') }}</button>
            </div>
            <p v-if="mutateError" class="error small">{{ mutateError }}</p>
          </div>
          <div class="resource-list">
            <div
              v-for="r in (data.resources || [])"
              :key="r.id"
              class="memory-card resource-card card-with-actions"
            >
              <div class="meta-row"><span class="meta-id small">{{ r.id }}</span><span class="meta-ts muted">{{ formatTs(r.created_at) }}</span></div>
              <div class="resource-url">{{ r.url }}</div>
              <div v-if="r.modality" class="muted small">modality: {{ r.modality }}</div>
              <div v-if="r.caption" class="resource-caption muted">{{ truncate(r.caption, 400) }}</div>
              <div class="card-actions">
                <button type="button" class="btn-link" @click="openForm('resource', 'edit', r)">{{ t('memory.edit') }}</button>
                <button type="button" class="btn-link danger" @click="deleteResource(r.id)">{{ t('memory.delete') }}</button>
              </div>
            </div>
          </div>
        </section>
        <section class="memory-section">
          <div class="section-head">
            <h2 class="section-title">{{ t('memory.relations') }} ({{ (data.category_item_relations || []).length }})</h2>
            <button type="button" class="btn small" @click="openForm('relation', 'add')">{{ t('memory.add') }}</button>
          </div>
          <div v-if="formMode && formMode.section === 'relation'" class="form-card">
            <input v-model="formData.item_id" type="text" :placeholder="t('memory.itemId')" class="input" />
            <input v-model="formData.category_id" type="text" :placeholder="t('memory.categoryId')" class="input" />
            <div class="form-actions">
              <button type="button" class="btn primary" :disabled="mutateLoading" @click="submitRelationForm">{{ t('memory.save') }}</button>
              <button type="button" class="btn secondary" @click="closeForm">{{ t('memory.cancel') }}</button>
            </div>
            <p v-if="mutateError" class="error small">{{ mutateError }}</p>
          </div>
          <div class="relations-list">
            <div
              v-for="rel in (data.category_item_relations || [])"
              :key="rel.id"
              class="memory-card relation-row card-with-actions"
            >
              <span class="rel-item">{{ rel.item_id }}</span>
              <span class="muted">→</span>
              <span class="rel-cat">{{ rel.category_id }}</span>
              <span class="muted small">({{ categoryName(rel.category_id) }} · {{ itemSummary(rel.item_id) }})</span>
              <div class="card-actions">
                <button type="button" class="btn-link danger" @click="deleteRelation(rel.id)">{{ t('memory.delete') }}</button>
              </div>
            </div>
          </div>
        </section>
        <section class="memory-section">
          <h2 class="section-title">{{ t('memory.chatMessages') }} ({{ (data.chat_messages || []).length }})</h2>
          <div class="chat-list">
            <div
              v-for="msg in (data.chat_messages || [])"
              :key="msg.id"
              class="memory-card chat-row"
              :class="'role-' + (msg.role || 'user')"
            >
              <div class="meta-row">
                <span class="chat-role">{{ msg.role }}</span>
                <span class="meta-ts muted">{{ formatTs(msg.created_at) }}</span>
                <span class="chat-session muted small">{{ msg.session_key }}</span>
              </div>
              <div class="chat-content">{{ truncate(msg.content, 600) }}</div>
              <div v-if="msg.extra && Object.keys(msg.extra).length" class="muted small pre">{{ JSON.stringify(msg.extra) }}</div>
            </div>
          </div>
        </section>
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
const data = ref(null)
const loading = ref(false)
const loadError = ref('')
const employeeName = ref('')
const formMode = ref(null)
const formData = ref({})
const mutateLoading = ref(false)
const mutateError = ref('')

function openForm(section, action, record = null) {
  mutateError.value = ''
  formMode.value = { section, action, id: record?.id }
  if (section === 'category') {
    formData.value = { name: record?.name ?? '', description: record?.description ?? '', summary: record?.summary ?? '' }
  } else if (section === 'item') {
    formData.value = { memory_type: record?.memory_type ?? 'profile', summary: record?.summary ?? '', resource_id: record?.resource_id ?? '' }
  } else if (section === 'resource') {
    formData.value = { url: record?.url ?? '', modality: record?.modality ?? 'conversation', local_path: record?.local_path ?? '', caption: record?.caption ?? '' }
  } else if (section === 'relation') {
    formData.value = { item_id: record?.item_id ?? '', category_id: record?.category_id ?? '' }
  }
}

function openFormForItemInCategory(categoryId) {
  mutateError.value = ''
  formMode.value = { section: 'item', action: 'add', addToCategoryId: categoryId }
  formData.value = { memory_type: 'profile', summary: '', resource_id: '', category_ids: [categoryId] }
}

function closeForm() {
  formMode.value = null
  mutateError.value = ''
}

async function submitCategoryForm() {
  mutateError.value = ''
  mutateLoading.value = true
  try {
    if (formMode.value.action === 'add') {
      await api.employees.memoryCategoryCreate(employeeId.value, { name: formData.value.name, description: formData.value.description, summary: formData.value.summary || undefined })
    } else {
      await api.employees.memoryCategoryUpdate(employeeId.value, formMode.value.id, { name: formData.value.name, description: formData.value.description, summary: formData.value.summary || undefined })
    }
    closeForm()
    await loadMemory()
  } catch (e) {
    mutateError.value = e.message || t('memory.failed')
  } finally {
    mutateLoading.value = false
  }
}

async function submitItemForm() {
  mutateError.value = ''
  mutateLoading.value = true
  try {
    if (formMode.value.action === 'add') {
      const payload = {
        memory_type: formData.value.memory_type || 'profile',
        summary: formData.value.summary,
        resource_id: formData.value.resource_id || undefined,
      }
      if (formMode.value.addToCategoryId) {
        payload.category_ids = [formMode.value.addToCategoryId]
      }
      await api.employees.memoryItemCreate(employeeId.value, payload)
    } else {
      await api.employees.memoryItemUpdate(employeeId.value, formMode.value.id, {
        summary: formData.value.summary,
        memory_type: formData.value.memory_type,
        resource_id: formData.value.resource_id || undefined,
      })
    }
    closeForm()
    await loadMemory()
  } catch (e) {
    mutateError.value = e.message || t('memory.failed')
  } finally {
    mutateLoading.value = false
  }
}

async function submitResourceForm() {
  mutateError.value = ''
  mutateLoading.value = true
  try {
    if (formMode.value.action === 'add') {
      await api.employees.memoryResourceCreate(employeeId.value, {
        url: formData.value.url,
        modality: formData.value.modality || 'conversation',
        local_path: formData.value.local_path || '',
        caption: formData.value.caption || undefined,
      })
    } else {
      await api.employees.memoryResourceUpdate(employeeId.value, formMode.value.id, {
        url: formData.value.url,
        modality: formData.value.modality,
        local_path: formData.value.local_path,
        caption: formData.value.caption,
      })
    }
    closeForm()
    await loadMemory()
  } catch (e) {
    mutateError.value = e.message || t('memory.failed')
  } finally {
    mutateLoading.value = false
  }
}

async function submitRelationForm() {
  mutateError.value = ''
  mutateLoading.value = true
  try {
    await api.employees.memoryRelationCreate(employeeId.value, { item_id: formData.value.item_id, category_id: formData.value.category_id })
    closeForm()
    await loadMemory()
  } catch (e) {
    mutateError.value = e.message || t('memory.failed')
  } finally {
    mutateLoading.value = false
  }
}

async function deleteCategory(cid) {
  if (!confirm(t('memory.confirmDelete'))) return
  try {
    await api.employees.memoryCategoryDelete(employeeId.value, cid)
    await loadMemory()
  } catch (e) {
    alert(e.message)
  }
}

async function deleteItem(iid) {
  if (!confirm(t('memory.confirmDelete'))) return
  try {
    await api.employees.memoryItemDelete(employeeId.value, iid)
    await loadMemory()
  } catch (e) {
    alert(e.message)
  }
}

async function deleteResource(rid) {
  if (!confirm(t('memory.confirmDelete'))) return
  try {
    await api.employees.memoryResourceDelete(employeeId.value, rid)
    await loadMemory()
  } catch (e) {
    alert(e.message)
  }
}

async function deleteRelation(relId) {
  if (!confirm(t('memory.confirmDelete'))) return
  try {
    await api.employees.memoryRelationDelete(employeeId.value, relId)
    await loadMemory()
  } catch (e) {
    alert(e.message)
  }
}

function truncate(str, maxLen) {
  if (typeof str !== 'string' || !str) return ''
  return str.length <= maxLen ? str : str.slice(0, maxLen) + '…'
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

function categoryName(categoryId) {
  if (!data.value || !categoryId) return ''
  const c = (data.value.categories || []).find((x) => x.id === categoryId)
  return c ? c.name : categoryId
}

function itemSummary(itemId) {
  if (!data.value || !itemId) return ''
  const i = (data.value.items || []).find((x) => x.id === itemId)
  return i ? truncate(i.summary, 60) : itemId
}

function itemsInCategory(categoryId) {
  if (!data.value || !categoryId) return []
  const relations = data.value.category_item_relations || []
  const itemIds = relations.filter((r) => r.category_id === categoryId).map((r) => r.item_id)
  const items = data.value.items || []
  return itemIds.map((id) => items.find((i) => i.id === id)).filter(Boolean)
}

async function loadMemory() {
  if (!employeeId.value) return
  loading.value = true
  loadError.value = ''
  try {
    data.value = await api.employees.memory(employeeId.value)
  } catch (e) {
    loadError.value = e.message || t('memory.loadFailed')
    data.value = null
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
  loadMemory()
})
watch(employeeId, () => {
  loadEmployeeName()
  loadMemory()
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
.muted { font-size: 0.875rem; color: var(--jt-text-muted); }
.memory-section { margin-bottom: 1.5rem; }
.memory-section:last-child { margin-bottom: 0; }
.section-title { font-size: 1rem; font-weight: 600; margin: 0 0 0.75rem; }
.section-head { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
.section-head .section-title { margin: 0; }
.form-card {
  border: 1px solid var(--jt-border);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 0.75rem;
  display: grid;
  gap: 0.5rem;
}
.form-card .input { padding: 0.4rem 0.5rem; border-radius: 4px; border: 1px solid var(--jt-border); font-size: 0.875rem; width: 100%; box-sizing: border-box; }
.form-card textarea.input { min-height: 4em; resize: vertical; }
.form-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.btn.small { padding: 0.35rem 0.65rem; font-size: 0.8125rem; }
.btn.primary { background: var(--jt-primary); color: #fff; border-color: var(--jt-primary); }
.btn.primary:hover:not(:disabled) { opacity: 0.9; }
.card-with-actions { position: relative; padding-bottom: 1.75rem; }
.card-actions { position: absolute; right: 0.5rem; bottom: 0.35rem; display: flex; gap: 0.5rem; }
.btn-link { background: none; border: none; padding: 0; font-size: 0.8125rem; color: var(--jt-primary); cursor: pointer; }
.btn-link:hover { text-decoration: underline; }
.btn-link.danger { color: #b91c1c; }
.memory-card {
  border: 1px solid var(--jt-border);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}
.memory-card:last-child { margin-bottom: 0; }
.meta-row { display: flex; align-items: center; gap: 0.5rem 0.75rem; flex-wrap: wrap; margin-bottom: 0.25rem; }
.meta-id { font-family: ui-monospace, monospace; font-size: 0.75rem; color: var(--jt-text-muted); }
.meta-id.small { font-size: 0.7rem; word-break: break-all; }
.meta-ts { font-size: 0.8125rem; }
.small { font-size: 0.8125rem; }
.pre { white-space: pre-wrap; word-break: break-word; }
.card-name { font-weight: 600; }
.card-desc { margin-top: 0.25rem; }
.card-summary { margin-top: 0.5rem; white-space: pre-wrap; word-break: break-word; }
.category-block { margin-bottom: 1rem; }
.category-block:last-child { margin-bottom: 0; }
.category-header { margin-bottom: 0.5rem; }
.category-items-wrap { margin-left: 0.75rem; padding-left: 0.75rem; border-left: 2px solid var(--jt-border); }
.category-empty { margin: 0.35rem 0 0.5rem; font-size: 0.875rem; }
.category-items-list { list-style: none; margin: 0.35rem 0 0.5rem; padding: 0; }
.category-item-row {
  display: flex;
  align-items: center;
  gap: 0.5rem 0.75rem;
  flex-wrap: wrap;
  padding: 0.4rem 0;
  border-bottom: 1px solid var(--jt-border);
  font-size: 0.875rem;
}
.category-item-row:last-child { border-bottom: none; }
.item-type-tag { font-weight: 500; min-width: 4.5em; }
.item-summary-text { flex: 1; min-width: 0; word-break: break-word; }
.add-item-btn { margin-top: 0.5rem; }
.category-inline-form { margin-top: 0.5rem; }
.item-card { display: grid; gap: 0.35rem 0.75rem; }
.item-card .item-summary { grid-column: 1 / -1; word-break: break-word; }
.item-type { font-weight: 500; }
.item-ts { font-size: 0.8125rem; }
.item-summary { word-break: break-word; }
.resource-url { font-family: ui-monospace, monospace; font-size: 0.8125rem; }
.resource-caption { margin-top: 0.35rem; white-space: pre-wrap; word-break: break-word; }
.relation-row { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.rel-item, .rel-cat { font-family: ui-monospace, monospace; font-size: 0.8rem; }
.chat-row { display: grid; gap: 0.35rem; }
.chat-row .chat-role { font-weight: 600; }
.chat-row.role-assistant .chat-role { color: var(--jt-primary); }
.chat-session { font-size: 0.75rem; }
.chat-content { white-space: pre-wrap; word-break: break-word; font-size: 0.875rem; }
</style>
